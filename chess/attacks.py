"""Precomputed attack tables for bitboard move generation.

This module contains precomputed attack patterns for all piece types.
"""

from __future__ import annotations

from .bitboard import (
    NOT_FILE_A,
    NOT_FILE_H,
    shift_east,
    shift_north,
    shift_north_east,
    shift_north_west,
    shift_south,
    shift_south_east,
    shift_south_west,
    shift_west,
    square_to_bit,
)
from .models import Square


def _generate_knight_attacks() -> list[int]:
    """Generate knight attack patterns for all squares."""
    attacks = [0] * 64
    for rank in range(8):
        for file in range(8):
            square = Square(rank, file)
            bit_pos = square_to_bit(square)
            bb = 1 << bit_pos
            
            # Knight moves: 2 squares in one direction, 1 square perpendicular
            attacks_bb = 0
            attacks_bb |= (bb << 17) & NOT_FILE_A  # 2 up, 1 right
            attacks_bb |= (bb << 15) & NOT_FILE_H  # 2 up, 1 left
            attacks_bb |= (bb << 10) & (NOT_FILE_A & (NOT_FILE_A << 1))  # 1 up, 2 right
            attacks_bb |= (bb << 6) & (NOT_FILE_H & (NOT_FILE_H >> 1))   # 1 up, 2 left
            attacks_bb |= (bb >> 17) & NOT_FILE_H  # 2 down, 1 left
            attacks_bb |= (bb >> 15) & NOT_FILE_A  # 2 down, 1 right
            attacks_bb |= (bb >> 10) & (NOT_FILE_H & (NOT_FILE_H >> 1))  # 1 down, 2 left
            attacks_bb |= (bb >> 6) & (NOT_FILE_A & (NOT_FILE_A << 1))   # 1 down, 2 right
            
            attacks[bit_pos] = attacks_bb & 0xFFFFFFFFFFFFFFFF
    return attacks


def _generate_king_attacks() -> list[int]:
    """Generate king attack patterns for all squares."""
    attacks = [0] * 64
    for rank in range(8):
        for file in range(8):
            square = Square(rank, file)
            bit_pos = square_to_bit(square)
            bb = 1 << bit_pos
            
            attacks_bb = 0
            attacks_bb |= shift_north(bb)
            attacks_bb |= shift_south(bb)
            attacks_bb |= shift_east(bb)
            attacks_bb |= shift_west(bb)
            attacks_bb |= shift_north_east(bb)
            attacks_bb |= shift_north_west(bb)
            attacks_bb |= shift_south_east(bb)
            attacks_bb |= shift_south_west(bb)
            
            attacks[bit_pos] = attacks_bb & 0xFFFFFFFFFFFFFFFF
    return attacks


def _generate_pawn_attacks() -> tuple[list[int], list[int]]:
    """Generate pawn attack patterns for white and black pawns.
    
    Returns:
        tuple[list[int], list[int]]: (white_attacks, black_attacks)
    """
    white_attacks = [0] * 64
    black_attacks = [0] * 64
    
    for rank in range(8):
        for file in range(8):
            square = Square(rank, file)
            bit_pos = square_to_bit(square)
            bb = 1 << bit_pos
            
            # White pawns attack diagonally forward (towards rank 0)
            white_attacks[bit_pos] = (shift_north_west(bb) | shift_north_east(bb)) & 0xFFFFFFFFFFFFFFFF
            
            # Black pawns attack diagonally forward (towards rank 7)
            black_attacks[bit_pos] = (shift_south_west(bb) | shift_south_east(bb)) & 0xFFFFFFFFFFFFFFFF
    
    return white_attacks, black_attacks


def _generate_ray(square: Square, dx: int, dy: int) -> int:
    """Generate a ray from a square in a given direction."""
    ray = 0
    rank, file = square.rank, square.file
    while True:
        rank += dx
        file += dy
        if not (0 <= rank < 8 and 0 <= file < 8):
            break
        ray |= 1 << (rank * 8 + file)
    return ray


def _generate_sliding_attacks(square: Square, occupied: int, directions: list[tuple[int, int]]) -> int:
    """Generate sliding piece attacks from a square given occupancy."""
    attacks = 0
    for dx, dy in directions:
        rank, file = square.rank, square.file
        while True:
            rank += dx
            file += dy
            if not (0 <= rank < 8 and 0 <= file < 8):
                break
            bit_pos = rank * 8 + file
            attacks |= 1 << bit_pos
            if occupied & (1 << bit_pos):
                break
    return attacks


def get_rook_attacks(square: Square, occupied: int) -> int:
    """Get rook attacks from a square given board occupancy."""
    return _generate_sliding_attacks(square, occupied, [(1, 0), (-1, 0), (0, 1), (0, -1)])


def get_bishop_attacks(square: Square, occupied: int) -> int:
    """Get bishop attacks from a square given board occupancy."""
    return _generate_sliding_attacks(square, occupied, [(1, 1), (1, -1), (-1, 1), (-1, -1)])


def get_queen_attacks(square: Square, occupied: int) -> int:
    """Get queen attacks from a square given board occupancy."""
    return get_rook_attacks(square, occupied) | get_bishop_attacks(square, occupied)


# Precompute non-sliding piece attacks
KNIGHT_ATTACKS = _generate_knight_attacks()
KING_ATTACKS = _generate_king_attacks()
PAWN_ATTACKS_WHITE, PAWN_ATTACKS_BLACK = _generate_pawn_attacks()


def get_knight_attacks(square: Square) -> int:
    """Get knight attacks from a square."""
    return KNIGHT_ATTACKS[square_to_bit(square)]


def get_king_attacks(square: Square) -> int:
    """Get king attacks from a square."""
    return KING_ATTACKS[square_to_bit(square)]


def get_pawn_attacks(square: Square, is_white: bool) -> int:
    """Get pawn attacks from a square."""
    bit_pos = square_to_bit(square)
    return PAWN_ATTACKS_WHITE[bit_pos] if is_white else PAWN_ATTACKS_BLACK[bit_pos]
