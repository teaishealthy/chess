from __future__ import annotations

from typing import Iterator, Self

from .fen import FenMixin
from .models import (
    BoardState,
    Color,
    KingNotFound,
    Move,
    Piece,
    PieceType,
    Square,
)
from .movegen import MoveGeneratorMixin


class Board(FenMixin, MoveGeneratorMixin):
    def __init__(self) -> None:
        # 8 ranks, 8 files
        self.squares: list[list[Piece | None]] = [[None] * 8 for _ in range(8)]
        self.last_move: Move | None = None
        self.to_move: Color = Color.WHITE
        self.castling_rights: dict[Color, dict[str, bool]] = {
            Color.WHITE: {"K": True, "Q": True},
            Color.BLACK: {"K": True, "Q": True},
        }
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1

    def copy(self) -> Self:
        """Copy the board

        Returns:
            Board: A new board instance with the same state as the original
        """
        board = type(self).from_fen(str(self))
        board.last_move = self.last_move

        return board

    def __copy__(self) -> Self:
        return self.copy()

    def __str__(self) -> str:
        return self.dump()

    def __repr__(self) -> str:
        return f"Board({self})"

    def make_move(self, start: Square, end: Square) -> Move:
        """Make a move on the board"""
        # Move a piece from start to end
        prev_piece = self.squares[end.rank][end.file]
        current_piece = self.squares[start.rank][start.file]
        assert current_piece is not None, "No piece at start square"
        captured_square: Square | None = None
        # Handle en passant capture
        if (
            current_piece.piece_type == PieceType.PAWN
            and start.file != end.file
            and prev_piece is None
        ):
            captured_square = Square(start.rank, end.file)
            prev_piece = self.squares[captured_square.rank][captured_square.file]
            self.squares[captured_square.rank][captured_square.file] = None
        elif prev_piece is not None:
            captured_square = end

        self.squares[end.rank][end.file] = self.squares[start.rank][start.file]
        self.squares[start.rank][start.file] = None
        self.last_move = Move(start, end, current_piece, prev_piece, captured_square)
        self.to_move = self.to_move.other
        return self.last_move

    def undo_move(self, move: Move) -> None:
        """Undo a move on the board"""
        self.squares[move.start.rank][move.start.file] = move.piece
        self.squares[move.end.rank][move.end.file] = move.captured_piece
        # Handle en passant capture restoration
        if (
            move.piece.piece_type == PieceType.PAWN
            and move.start.file != move.end.file
            and move.captured_square is not None
            and move.captured_square != move.end
        ):
            self.squares[move.captured_square.rank][
                move.captured_square.file
            ] = move.captured_piece
            self.squares[move.end.rank][move.end.file] = None

        self.last_move = None  # Could be improved to track history
        self.to_move = self.to_move.other

    def find_king(self, color: Color) -> Square | None:
        """Find the king of the given color"""
        for row_idx, row in enumerate(self.squares):
            for square_idx, square in enumerate(row):
                if (
                    square is not None
                    and square.piece_type == PieceType.KING
                    and square.color == color
                ):
                    return Square(row_idx, square_idx)
        return None

    def __iter__(self) -> Iterator[tuple[Piece, Square]]:
        for rank_idx, rank in enumerate(self.squares):
            for square_idx, piece in enumerate(rank):
                if piece is not None:
                    yield piece, Square(rank_idx, square_idx)

    def in_check(self, color: Color) -> tuple[Square, Piece] | None:
        """Check if the given color is in check"""
        king = self.find_king(color)
        if king is None:
            raise KingNotFound(f"Could not find king of color {color}")

        return self.is_attacked(king, color.other)

    def state(self, color: Color) -> BoardState:
        """Determine the state of the board for the given color"""
        has_legal_move = False
        for piece, square in self:
            if piece.color == color and self.has_any_legal_move(square):
                has_legal_move = True
                break

        in_check = self.in_check(color) is not None
        if has_legal_move:
            return BoardState.CHECK if in_check else BoardState.NORMAL

        # No legal moves — checkmate or stalemate
        return BoardState.CHECKMATE if in_check else BoardState.STALEMATE

    @property
    def stalemate(self) -> bool:
        """Check if the board is in stalemate"""
        return (
            self.state(Color.WHITE) == BoardState.STALEMATE
            or self.state(Color.BLACK) == BoardState.STALEMATE
        )
