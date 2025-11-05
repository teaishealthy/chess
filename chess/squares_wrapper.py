"""Wrapper for bitboard squares to maintain backward compatibility."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bitboard_board import BitBoard
from .models import Piece


class SquaresWrapper:
    """A wrapper that makes bitboard act like a 2D array of squares."""

    def __init__(self, board: BitBoard) -> None:
        self._board = board
        self._rows: list[RowWrapper] = [RowWrapper(board, rank) for rank in range(8)]

    def __getitem__(self, rank: int) -> RowWrapper:
        return self._rows[rank]

    def __setitem__(self, rank: int, value: list[Piece | None]) -> None:
        for file, piece in enumerate(value):
            self._board._set_piece_from_squares(rank, file, piece)
    
    def __str__(self) -> str:
        """Convert to string representation matching 2D list format."""
        rows = []
        for rank in range(8):
            row = []
            for file in range(8):
                from .models import Square
                piece = self._board._get_piece_at(Square(rank, file))
                row.append(piece)
            rows.append(row)
        return str(rows)
    
    def __repr__(self) -> str:
        return self.__str__()


class RowWrapper:
    """A wrapper for a row in the bitboard."""

    def __init__(self, board: BitBoard, rank: int) -> None:
        self._board = board
        self._rank = rank

    def __getitem__(self, file: int) -> Piece | None:
        from .models import Square
        return self._board._get_piece_at(Square(self._rank, file))

    def __setitem__(self, file: int, piece: Piece | None) -> None:
        self._board._set_piece_from_squares(self._rank, file, piece)
