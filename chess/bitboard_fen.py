"""FEN parsing and serialization for bitboard-based board."""

from __future__ import annotations

from .bitboard import set_bit
from .bitboard_board import BitBoard
from .models import Color, Move, Piece, PieceType, Square


class BitBoardFenMixin(BitBoard):
    """FEN support for bitboard-based board."""

    def load(self, fen: str) -> None:
        """Load a FEN string into the board."""
        (
            positions,
            to_move,
            castling_rights,
            en_passant_target,
            halfmove_clock,
            fullmove_number,
        ) = fen.split(" ")

        # Clear all bitboards
        for color in Color:
            for piece_type in PieceType:
                self.pieces[color][piece_type] = 0

        # Parse piece positions
        rank = 0
        file = 0
        for char in positions:
            if char == "/":
                rank += 1
                file = 0
            elif char.isnumeric():
                file += int(char)
            else:
                color = Color.WHITE if char.isupper() else Color.BLACK
                piece_type = PieceType(char.lower())
                square = Square(rank, file)
                self.pieces[color][piece_type] = set_bit(
                    self.pieces[color][piece_type], square
                )
                file += 1

        self._update_occupancy()

        # Parse side to move
        self.to_move = Color.WHITE if to_move == "w" else Color.BLACK

        # Parse castling rights
        self.castling_rights = {
            Color.WHITE: {"K": "K" in castling_rights, "Q": "Q" in castling_rights},
            Color.BLACK: {"K": "k" in castling_rights, "Q": "q" in castling_rights},
        }

        # Parse en passant target
        self.last_move = None
        if en_passant_target != "-":
            ep_square = Square.from_notation(en_passant_target)
            direction = self.to_move.direction
            pawn_rank = ep_square.rank - direction
            pawn_start = Square(pawn_rank + direction * 2, ep_square.file)
            pawn_end = Square(pawn_rank, ep_square.file)
            pawn_piece = self._get_piece_at(pawn_end)
            assert (
                pawn_piece is not None
                and pawn_piece.piece_type == PieceType.PAWN
                and pawn_piece.color == self.to_move.other
            ), "Invalid en passant target in FEN"
            self.last_move = Move(
                start=pawn_start,
                end=pawn_end,
                piece=pawn_piece,
            )

        # Parse halfmove clock and fullmove number
        self.halfmove_clock = int(halfmove_clock)
        self.fullmove_number = int(fullmove_number)

        # Update king positions cache
        self._recompute_king_positions()

    def dump(self) -> str:
        """Dump the board to a FEN string."""
        # Convert bitboards to FEN position string
        fen_ranks: list[str] = []
        for rank in range(8):
            fen_rank = ""
            empty_count = 0
            for file in range(8):
                square = Square(rank, file)
                piece = self._get_piece_at(square)
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count:
                        fen_rank += str(empty_count)
                        empty_count = 0
                    fen_rank += (
                        piece.piece_type.value
                        if piece.color == Color.BLACK
                        else piece.piece_type.value.upper()
                    )
            if empty_count:
                fen_rank += str(empty_count)
            fen_ranks.append(fen_rank)

        positions = "/".join(fen_ranks)
        to_move_char = "w" if self.to_move == Color.WHITE else "b"

        # Castling rights
        castling_chars = ""
        if self.castling_rights[Color.WHITE]["K"]:
            castling_chars += "K"
        if self.castling_rights[Color.WHITE]["Q"]:
            castling_chars += "Q"
        if self.castling_rights[Color.BLACK]["K"]:
            castling_chars += "k"
        if self.castling_rights[Color.BLACK]["Q"]:
            castling_chars += "q"
        castling_chars = castling_chars or "-"

        # En passant target
        en_passant_char = "-"
        if self.last_move is not None and self.last_move.en_passant_target:
            ep_rank = self.last_move.end.rank - self.last_move.piece.color.direction
            ep_file = self.last_move.end.file
            en_passant_char = Square(ep_rank, ep_file).to_notation()

        return (
            f"{positions} {to_move_char} {castling_chars} "
            f"{en_passant_char} {self.halfmove_clock} {self.fullmove_number}"
        )

    @classmethod
    def from_fen(cls, fen: str):
        """Create a board from a FEN string."""
        board = cls()
        board.load(fen)
        return board

    @classmethod
    def starting_position(cls):
        """Create the starting position for a chess game."""
        return cls.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
