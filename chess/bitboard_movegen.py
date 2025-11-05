"""Move generation for bitboard-based chess board."""

from __future__ import annotations

import functools
from typing import Iterable, Iterator

from .attacks import (
    get_bishop_attacks,
    get_king_attacks,
    get_knight_attacks,
    get_pawn_attacks,
    get_queen_attacks,
    get_rook_attacks,
)
from .bitboard import (
    RANK_MASKS,
    get_bit,
    iter_squares,
    shift_north,
    shift_south,
    square_to_bit,
)
from .bitboard_board import BitBoard
from .models import (
    Color,
    KingNotFound,
    Piece,
    PieceType,
    Square,
)


class BitBoardMoveGenMixin(BitBoard):
    """Move generation mixin for bitboard-based board."""

    def legal_moves(self, square: Square) -> Iterator[Square]:
        """Generate legal moves for a piece at a square."""
        piece = self._get_piece_at(square)
        assert piece is not None, "No piece at given square"

        candidates = self._get_pseudo_legal_moves(square, piece)
        return self._legal_targets(square, candidates)

    def _get_pseudo_legal_moves(self, square: Square, piece: Piece) -> Iterator[Square]:
        """Get pseudo-legal moves (before checking if they leave king in check)."""
        if piece.piece_type == PieceType.PAWN:
            return self._pawn_candidates(square, piece)
        elif piece.piece_type == PieceType.KNIGHT:
            return self._knight_moves(square, piece)
        elif piece.piece_type == PieceType.BISHOP:
            return self._bishop_moves(square, piece)
        elif piece.piece_type == PieceType.ROOK:
            return self._rook_moves(square, piece)
        elif piece.piece_type == PieceType.QUEEN:
            return self._queen_moves(square, piece)
        elif piece.piece_type == PieceType.KING:
            return self._king_moves(square, piece)
        else:  # pragma: no cover
            raise ValueError(f"Unknown piece type: {piece.piece_type}")

    def attack_squares(self, square: Square) -> Iterator[Square]:
        """Get all squares attacked by a piece."""
        piece = self._get_piece_at(square)
        assert piece is not None, "No piece at given square"

        if piece.piece_type == PieceType.PAWN:
            return self._pawn_attacks(square, piece)
        elif piece.piece_type == PieceType.KNIGHT:
            attacks_bb = get_knight_attacks(square)
            return iter_squares(attacks_bb)
        elif piece.piece_type == PieceType.BISHOP:
            return self._bishop_moves(square, piece)
        elif piece.piece_type == PieceType.ROOK:
            return self._rook_moves(square, piece)
        elif piece.piece_type == PieceType.QUEEN:
            return self._queen_moves(square, piece)
        elif piece.piece_type == PieceType.KING:
            attacks_bb = get_king_attacks(square)
            return iter_squares(attacks_bb)
        else:  # pragma: no cover
            raise ValueError(f"Unknown piece type: {piece.piece_type}")

    def has_any_legal_move(self, square: Square) -> bool:
        """Check if a piece has any legal moves."""
        return next(self.legal_moves(square), None) is not None

    def is_attacked(
        self, square: Square, by_color: Color
    ) -> tuple[Square, Piece] | None:
        """Check if a square is attacked by a given color."""
        # Check knight attacks
        knight_attacks = get_knight_attacks(square)
        knight_bb = self.pieces[by_color][PieceType.KNIGHT] & knight_attacks
        if knight_bb:
            attacker_square = next(iter_squares(knight_bb))
            return (attacker_square, Piece(by_color, PieceType.KNIGHT))

        # Check pawn attacks
        pawn_attacks_bb = get_pawn_attacks(square, by_color == Color.BLACK)
        pawn_bb = self.pieces[by_color][PieceType.PAWN] & pawn_attacks_bb
        if pawn_bb:
            attacker_square = next(iter_squares(pawn_bb))
            # Check for en passant vulnerability
            this_piece = self._get_piece_at(square)
            last_move = self.last_move
            if (
                last_move is not None
                and last_move.en_passant_target
                and last_move.piece is this_piece
            ):
                # Check if any enemy pawn is adjacent
                for file_delta in (-1, 1):
                    adjacent_file = square.file + file_delta
                    if 0 <= adjacent_file < 8:
                        adjacent_square = Square(square.rank, adjacent_file)
                        occupant = self._get_piece_at(adjacent_square)
                        if (
                            occupant is not None
                            and occupant.color == by_color
                            and occupant.piece_type == PieceType.PAWN
                        ):
                            return (adjacent_square, occupant)
            return (attacker_square, Piece(by_color, PieceType.PAWN))

        # Check king attacks
        king_attacks = get_king_attacks(square)
        king_bb = self.pieces[by_color][PieceType.KING] & king_attacks
        if king_bb:
            attacker_square = next(iter_squares(king_bb))
            return (attacker_square, Piece(by_color, PieceType.KING))

        # Check sliding piece attacks (rook, bishop, queen)
        # Rook attacks
        rook_attacks = get_rook_attacks(square, self.occupancy)
        rook_bb = self.pieces[by_color][PieceType.ROOK] & rook_attacks
        if rook_bb:
            attacker_square = next(iter_squares(rook_bb))
            return (attacker_square, Piece(by_color, PieceType.ROOK))

        # Bishop attacks
        bishop_attacks = get_bishop_attacks(square, self.occupancy)
        bishop_bb = self.pieces[by_color][PieceType.BISHOP] & bishop_attacks
        if bishop_bb:
            attacker_square = next(iter_squares(bishop_bb))
            return (attacker_square, Piece(by_color, PieceType.BISHOP))

        # Queen attacks (rook + bishop)
        queen_attacks = rook_attacks | bishop_attacks
        queen_bb = self.pieces[by_color][PieceType.QUEEN] & queen_attacks
        if queen_bb:
            attacker_square = next(iter_squares(queen_bb))
            return (attacker_square, Piece(by_color, PieceType.QUEEN))

        return None

    def _legal_targets(
        self, start: Square, candidates: Iterable[Square]
    ) -> Iterator[Square]:
        """Filter pseudo-legal moves to only legal moves."""
        origin = self._get_piece_at(start)
        assert origin is not None, "No piece at start square"

        color = origin.color
        for target in candidates:
            assert target.check_limits(), "Target square out of bounds"

            occupant = self._get_piece_at(target)
            if occupant is not None and occupant.piece_type == PieceType.KING:
                continue
            
            previous_last_move = self.last_move
            move = self.make_move(start, target)
            legal = False
            try:
                if not self.in_check(color):
                    legal = True
            except KingNotFound:
                legal = True
            self.undo_move(move)
            self.last_move = previous_last_move
            if legal:
                yield target

    def _pawn_candidates(self, square: Square, piece: Piece) -> Iterator[Square]:
        """Generate pawn move candidates."""
        forward = piece.color.direction
        home_rank = 6 if piece.color == Color.WHITE else 1

        # Forward moves
        one_forward = Square(square.rank + forward, square.file)
        if one_forward.check_limits() and not get_bit(self.occupancy, one_forward):
            yield one_forward
            # Double push from home rank
            if square.rank == home_rank:
                two_forward = Square(square.rank + forward * 2, square.file)
                if two_forward.check_limits() and not get_bit(self.occupancy, two_forward):
                    yield two_forward

        # Captures
        for target in self._pawn_attacks(square, piece):
            occupant = self._get_piece_at(target)
            if occupant is not None and occupant.color != piece.color:
                yield target

        # En passant
        last_move = self.last_move
        if (
            last_move is not None
            and last_move.en_passant_target
            and last_move.piece.color != piece.color
            and last_move.end.rank == square.rank
        ):
            required_rank = 3 if piece.color == Color.WHITE else 4
            if square.rank == required_rank:
                for file_delta in (-1, 1):
                    if square.file + file_delta == last_move.end.file:
                        capture_square = Square(square.rank + forward, square.file + file_delta)
                        if capture_square.check_limits() and not get_bit(
                            self.occupancy, capture_square
                        ):
                            yield capture_square

    def _pawn_attacks(self, square: Square, piece: Piece) -> Iterator[Square]:
        """Generate pawn attack squares."""
        attacks_bb = get_pawn_attacks(square, piece.color == Color.WHITE)
        return iter_squares(attacks_bb)

    def _knight_moves(self, square: Square, piece: Piece) -> Iterator[Square]:
        """Generate knight moves."""
        attacks_bb = get_knight_attacks(square)
        # Remove friendly pieces
        targets_bb = attacks_bb & ~self.color_occupancy[piece.color]
        return iter_squares(targets_bb)

    def _bishop_moves(self, square: Square, piece: Piece) -> Iterator[Square]:
        """Generate bishop moves."""
        attacks_bb = get_bishop_attacks(square, self.occupancy)
        # Remove friendly pieces
        targets_bb = attacks_bb & ~self.color_occupancy[piece.color]
        return iter_squares(targets_bb)

    def _rook_moves(self, square: Square, piece: Piece) -> Iterator[Square]:
        """Generate rook moves."""
        attacks_bb = get_rook_attacks(square, self.occupancy)
        # Remove friendly pieces
        targets_bb = attacks_bb & ~self.color_occupancy[piece.color]
        return iter_squares(targets_bb)

    def _queen_moves(self, square: Square, piece: Piece) -> Iterator[Square]:
        """Generate queen moves."""
        attacks_bb = get_queen_attacks(square, self.occupancy)
        # Remove friendly pieces
        targets_bb = attacks_bb & ~self.color_occupancy[piece.color]
        return iter_squares(targets_bb)

    def _king_moves(self, square: Square, piece: Piece) -> Iterator[Square]:
        """Generate king moves."""
        attacks_bb = get_king_attacks(square)
        # Remove friendly pieces
        targets_bb = attacks_bb & ~self.color_occupancy[piece.color]
        return iter_squares(targets_bb)

    def in_check(self, color: Color) -> tuple[Square, Piece] | None:
        """Check if the given color is in check."""
        king = self.find_king(color)
        if king is None:
            raise KingNotFound(f"Could not find king of color {color}")

        return self.is_attacked(king, color.other)
