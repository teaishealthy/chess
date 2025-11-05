from __future__ import annotations

import functools
from typing import Iterable, Iterator

from .models import (
    BISHOP_DIRECTIONS,
    KING_OFFSETS,
    KNIGHT_OFFSETS,
    QUEEN_DIRECTIONS,
    ROOK_DIRECTIONS,
    BoardProtocol,
    Color,
    Direction,
    KingNotFound,
    Piece,
    PieceType,
    Square,
)


class MoveGeneratorMixin(BoardProtocol):
    """Generate moves and attacks for a board."""

    def legal_moves(self, square: Square) -> Iterator[Square]:
        piece = self.squares[square.rank][square.file]
        assert piece is not None, "No piece at given square"

        if piece.piece_type == PieceType.PAWN:
            candidates = self._pawn_candidates(square, piece)
        elif piece.piece_type == PieceType.ROOK:
            candidates = self._sliding_moves(square, piece, ROOK_DIRECTIONS)
        elif piece.piece_type == PieceType.BISHOP:
            candidates = self._sliding_moves(square, piece, BISHOP_DIRECTIONS)
        elif piece.piece_type == PieceType.QUEEN:
            candidates = self._sliding_moves(square, piece, QUEEN_DIRECTIONS)
        elif piece.piece_type == PieceType.KNIGHT:
            candidates = self._offset_moves(square, piece, KNIGHT_OFFSETS)
        elif piece.piece_type == PieceType.KING:
            candidates = self._offset_moves(square, piece, KING_OFFSETS)
        else:  # pragma: no cover
            raise ValueError(f"Unknown piece type: {piece.piece_type}")

        return self._legal_targets(square, candidates)

    def attack_squares(self, square: Square) -> Iterator[Square]:
        piece = self.squares[square.rank][square.file]
        assert piece is not None, "No piece at given square"

        if piece.piece_type == PieceType.PAWN:
            return self._pawn_attacks(square, piece)
        if piece.piece_type == PieceType.ROOK:
            return self._sliding_moves(square, piece, ROOK_DIRECTIONS)
        if piece.piece_type == PieceType.BISHOP:
            return self._sliding_moves(square, piece, BISHOP_DIRECTIONS)
        if piece.piece_type == PieceType.QUEEN:
            return self._sliding_moves(square, piece, QUEEN_DIRECTIONS)
        if piece.piece_type == PieceType.KNIGHT:
            return self._offset_attacks(square, KNIGHT_OFFSETS)
        if piece.piece_type == PieceType.KING:
            return self._offset_attacks(square, KING_OFFSETS)
        raise ValueError(f"Unknown piece type: {piece.piece_type}")  # pragma: no cover

    def has_any_legal_move(self, square: Square) -> bool:
        return next(self.legal_moves(square), None) is not None

    def is_attacked(
        self, square: Square, by_color: Color
    ) -> tuple[Square, Piece] | None:
        for direction in QUEEN_DIRECTIONS:
            for target in self._ray(square, direction):
                piece = self.squares[target.rank][target.file]
                if piece is None:
                    continue
                if piece.color == by_color:
                    if piece.piece_type == PieceType.QUEEN:
                        return (target, piece)
                    if (
                        piece.piece_type == PieceType.ROOK
                        and direction in ROOK_DIRECTIONS
                    ):
                        return (target, piece)
                    if (
                        piece.piece_type == PieceType.BISHOP
                        and direction in BISHOP_DIRECTIONS
                    ):
                        return (target, piece)
                    break
                break

        for target in self._offset_attacks(square, KNIGHT_OFFSETS):
            piece = self.squares[target.rank][target.file]
            if (
                piece is not None
                and piece.color == by_color
                and piece.piece_type == PieceType.KNIGHT
            ):
                return (target, piece)

        forward = by_color.direction
        for candidate in (Square(square.rank - forward, square.file - 1), Square(square.rank - forward, square.file + 1)):
            if candidate.check_limits():
                piece = self.squares[candidate.rank][candidate.file]
                if (
                    piece is not None
                    and piece.color == by_color
                    and piece.piece_type == PieceType.PAWN
                ):
                    return (candidate, piece)

        this_piece = self.squares[square.rank][square.file]
        last_move = self.last_move
        if (
            last_move is not None
            and last_move.en_passant_target
            and last_move.piece is this_piece
        ):
            for file_delta in (-1, 1):
                adjacent_square = Square(square.rank, square.file + file_delta)
                if adjacent_square.check_limits():
                    occupant = self.squares[adjacent_square.rank][adjacent_square.file]
                    if occupant is not None and occupant == Piece(
                        by_color, PieceType.PAWN
                    ):
                        return (adjacent_square, occupant)

        for target in self._offset_attacks(square, KING_OFFSETS):
            piece = self.squares[target.rank][target.file]
            if (
                piece is not None
                and piece.color == by_color
                and piece.piece_type == PieceType.KING
            ):
                return (target, piece)

        return None

    def _legal_targets(
        self, start: Square, candidates: Iterable[Square]
    ) -> Iterator[Square]:
        origin = self.squares[start.rank][start.file]
        assert origin is not None, "No piece at start square"

        color = origin.color
        for target in candidates:
            assert target.check_limits(), "Target square out of bounds"

            occupant = self.squares[target.rank][target.file]
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
        forward = piece.color.direction
        home_rank = 6 if piece.color == Color.WHITE else 1

        one_forward = Square(square.rank + forward, square.file)
        if self._is_empty(one_forward):
            yield one_forward
            two_forward = Square(square.rank + forward * 2, square.file)
            if square.rank == home_rank and self._is_empty(two_forward):
                yield two_forward

        for target in self._pawn_attacks(square, piece):
            occupant = self.squares[target.rank][target.file]
            if occupant is not None and occupant.color != piece.color:
                yield target

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
                        if capture_square.check_limits() and self._is_empty(
                            capture_square
                        ):
                            yield capture_square

    def _is_empty(self, square: Square) -> bool:
        assert square.check_limits(), "Square out of bounds"
        return self.squares[square.rank][square.file] is None

    @functools.cache
    def _ray(self, square: Square, delta: Direction) -> list[Square]:
        target = Square(square.rank + delta[0], square.file + delta[1])
        l: list[Square] = []
        while target.check_limits():
            l.append(target)
            target = Square(target.rank + delta[0], target.file + delta[1])
        return l

    def _sliding_moves(
        self, square: Square, piece: Piece, directions: Iterable[Direction]
    ) -> Iterator[Square]:
        for direction in directions:
            for target in self._ray(square, direction):
                occupant = self.squares[target.rank][target.file]
                if occupant is None:
                    yield target
                    continue
                if occupant.color != piece.color:
                    yield target
                break

    def _offset_moves(
        self, square: Square, piece: Piece, offsets: Iterable[Direction]
    ) -> Iterator[Square]:
        for delta in offsets:
            target = Square(square.rank + delta[0], square.file + delta[1])
            if not target.check_limits():
                continue
            occupant = self.squares[target.rank][target.file]
            if occupant is None or occupant.color != piece.color:
                yield target

    def _offset_attacks(
        self, square: Square, offsets: Iterable[Direction]
    ) -> Iterator[Square]:
        for delta in offsets:
            target = Square(square.rank + delta[0], square.file + delta[1])
            if target.check_limits():
                yield target

    def _pawn_attacks(self, square: Square, piece: Piece) -> Iterator[Square]:
        forward = piece.color.direction
        for candidate in (Square(square.rank + forward, square.file - 1), Square(square.rank + forward, square.file + 1)):
            if candidate.check_limits():
                yield candidate
