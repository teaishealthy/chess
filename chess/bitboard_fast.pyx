# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: nonecheck=False
# cython: cdivision=True
# cython: infer_types=True

"""Optimized Cython functions for bitboard operations."""

cimport cython
from libc.stdint cimport int64_t, uint64_t

@cython.cfunc
@cython.inline
cdef inline int64_t square_to_bit_fast(int rank, int file) nogil:
    """Fast square to bit conversion."""
    return rank * 8 + file

@cython.cfunc  
@cython.inline
cdef inline bint get_bit_fast(uint64_t bitboard, int rank, int file) nogil:
    """Fast get bit."""
    return (bitboard & (1ULL << (rank * 8 + file))) != 0

cpdef void update_occupancy_fast(
    list piece_bbs_white,
    list piece_bbs_black,
    uint64_t[:] color_occ,
):
    """Fast occupancy update using C types."""
    cdef uint64_t white_occ = 0
    cdef uint64_t black_occ = 0
    cdef int i
    
    for i in range(6):
        white_occ |= <uint64_t>piece_bbs_white[i]
        black_occ |= <uint64_t>piece_bbs_black[i]
    
    color_occ[0] = white_occ
    color_occ[1] = black_occ
