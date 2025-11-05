"""Bitboard-based chess board implementation.

This module replaces the old 2D array implementation with a more efficient
bitboard-based representation.
"""

from __future__ import annotations

from .bitboard_fen import BitBoardFenMixin
from .bitboard_movegen import BitBoardMoveGenMixin
from .bitboard_perft import BitBoardPerftMixin
from .models import (
    BoardState,
    Color,
    KingNotFound,
    Move,
    Piece,
    PieceType,
    Square,
)

# Re-export commonly used classes
__all__ = [
    'Board',
    'BoardState',
    'Color',
    'KingNotFound',
    'Move',
    'Piece',
    'PieceType',
    'Square',
]


class Board(BitBoardFenMixin, BitBoardMoveGenMixin, BitBoardPerftMixin):
    """Chess board using bitboard representation.
    
    This class combines FEN parsing, move generation, and perft functionality
    using an efficient bitboard representation where each piece type and color
    is represented as a 64-bit integer.
    """
    pass
