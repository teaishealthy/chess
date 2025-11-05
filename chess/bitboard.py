"""Bitboard utilities for chess board representation.

A bitboard is a 64-bit integer where each bit represents a square on the chess board.
The squares are numbered from 0-63:
  - Square 0 = a8 (rank 0, file 0)
  - Square 7 = h8 (rank 0, file 7)
  - Square 56 = a1 (rank 7, file 0)
  - Square 63 = h1 (rank 7, file 7)
"""

from __future__ import annotations

from typing import Iterator

from .models import Square


def square_to_bit(square: Square) -> int:
    """Convert a Square to a bit position (0-63)."""
    return square.rank * 8 + square.file


def bit_to_square(bit: int) -> Square:
    """Convert a bit position (0-63) to a Square."""
    return Square(bit // 8, bit % 8)


def set_bit(bitboard: int, square: Square) -> int:
    """Set the bit at the given square."""
    return bitboard | (1 << square_to_bit(square))


def clear_bit(bitboard: int, square: Square) -> int:
    """Clear the bit at the given square."""
    return bitboard & ~(1 << square_to_bit(square))


def get_bit(bitboard: int, square: Square) -> bool:
    """Check if the bit at the given square is set."""
    return bool(bitboard & (1 << square_to_bit(square)))


def pop_lsb(bitboard: int) -> tuple[int, int]:
    """Remove and return the least significant bit position.
    
    Returns:
        tuple[int, int]: (remaining bitboard, bit position)
    """
    bit = (bitboard & -bitboard).bit_length() - 1
    return bitboard & (bitboard - 1), bit


def iter_bits(bitboard: int) -> Iterator[int]:
    """Iterate over all set bits in the bitboard."""
    while bitboard:
        bitboard, bit = pop_lsb(bitboard)
        yield bit


def iter_squares(bitboard: int) -> Iterator[Square]:
    """Iterate over all squares where bits are set."""
    for bit in iter_bits(bitboard):
        yield bit_to_square(bit)


def count_bits(bitboard: int) -> int:
    """Count the number of set bits in the bitboard."""
    return bin(bitboard).count('1')


# Precompute some useful bitboards
RANK_MASKS = [0xFF << (i * 8) for i in range(8)]
FILE_MASKS = [0x0101010101010101 << i for i in range(8)]

# Edge masks
RANK_1 = RANK_MASKS[7]
RANK_8 = RANK_MASKS[0]
FILE_A = FILE_MASKS[0]
FILE_H = FILE_MASKS[7]

NOT_FILE_A = ~FILE_A
NOT_FILE_H = ~FILE_H
NOT_RANK_1 = ~RANK_1
NOT_RANK_8 = ~RANK_8


def shift_north(bitboard: int) -> int:
    """Shift bitboard one rank towards rank 1 (north)."""
    return (bitboard >> 8) & 0xFFFFFFFFFFFFFFFF


def shift_south(bitboard: int) -> int:
    """Shift bitboard one rank towards rank 8 (south)."""
    return (bitboard << 8) & 0xFFFFFFFFFFFFFFFF


def shift_east(bitboard: int) -> int:
    """Shift bitboard one file towards file h (east)."""
    return (bitboard << 1) & NOT_FILE_A & 0xFFFFFFFFFFFFFFFF


def shift_west(bitboard: int) -> int:
    """Shift bitboard one file towards file a (west)."""
    return (bitboard >> 1) & NOT_FILE_H & 0xFFFFFFFFFFFFFFFF


def shift_north_east(bitboard: int) -> int:
    """Shift bitboard diagonally north-east."""
    return shift_north(shift_east(bitboard))


def shift_north_west(bitboard: int) -> int:
    """Shift bitboard diagonally north-west."""
    return shift_north(shift_west(bitboard))


def shift_south_east(bitboard: int) -> int:
    """Shift bitboard diagonally south-east."""
    return shift_south(shift_east(bitboard))


def shift_south_west(bitboard: int) -> int:
    """Shift bitboard diagonally south-west."""
    return shift_south(shift_west(bitboard))


def print_bitboard(bitboard: int) -> None:
    """Print a bitboard in a human-readable format (for debugging)."""
    for rank in range(8):
        for file in range(8):
            square = Square(rank, file)
            if get_bit(bitboard, square):
                print('1', end=' ')
            else:
                print('.', end=' ')
        print()
    print()
