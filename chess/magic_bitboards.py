"""Magic bitboard implementation for fast sliding piece attack generation.

Magic bitboards use multiplication and lookup tables to achieve O(1) attack generation
for sliding pieces (rooks, bishops, queens) instead of iterative ray generation.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Square

from .bitboard import square_to_bit


# Magic numbers for rooks (64 squares)
ROOK_MAGICS = [
    0xa8002c000108020, 0x6c00049b0002001, 0x100200010090040, 0x2480041000800801,
    0x280028004000800, 0x900410008040022, 0x280020001001080, 0x2880002041000080,
    0xa000800080400034, 0x4808020004000, 0x2290802004801000, 0x411000d00100020,
    0x402800800040080, 0xb000401004208, 0x2409000100040200, 0x1002100004082,
    0x22878001e24000, 0x1090810021004010, 0x801030040200012, 0x500808008001000,
    0xa08018014000880, 0x8000808004000200, 0x201008080010200, 0x801020000441091,
    0x800080204005, 0x1040200040100048, 0x120200402082, 0xd14880480100080,
    0x12040280080080, 0x100040080020080, 0x9020010080800200, 0x813241200148449,
    0x491604001800080, 0x100401000402001, 0x4820010021001040, 0x400402202000812,
    0x209009005000802, 0x810800601800400, 0x4301083214000150, 0x204026458e001401,
    0x40204000808000, 0x8001008040010020, 0x8410820820420010, 0x1003001000090020,
    0x804040008008080, 0x12000810020004, 0x1000100200040208, 0x430000a044020001,
    0x280009023410300, 0xe0100040002240, 0x200100401700, 0x2244100408008080,
    0x8000400801980, 0x2000810040200, 0x8010100228810400, 0x2000009044210200,
    0x4080008040102101, 0x40002080411d01, 0x2005524060000901, 0x502001008400422,
    0x489a000810200402, 0x1004400080a13, 0x4000011008020084, 0x26002114058042,
]

# Magic numbers for bishops (64 squares)
BISHOP_MAGICS = [
    0x89a1121896040240, 0x2004844802002010, 0x2068080051921000, 0x62880a0220200808,
    0x4042004000000, 0x100822020200011, 0xc00444222012000a, 0x28808801216001,
    0x400492088408100, 0x201c401040c0084, 0x840800910a0010, 0x82080240060,
    0x2000840504006000, 0x30010c4108405004, 0x1008005410080802, 0x8144042209100900,
    0x208081020014400, 0x4800201208ca00, 0xf18140408012008, 0x1004002802102001,
    0x841000820080811, 0x40200200a42008, 0x800054042000, 0x88010400410c9000,
    0x520040470104290, 0x1004040051500081, 0x2002081833080021, 0x400c00c010142,
    0x941408200c002000, 0x658810000806011, 0x188071040440a00, 0x4800404002011c00,
    0x104442040404200, 0x511080202091021, 0x4022401120400, 0x80c0040400080120,
    0x8040010040820802, 0x480810700020090, 0x102008e00040242, 0x809005202050100,
    0x8002024220104080, 0x431008804142000, 0x19001802081400, 0x200014208040080,
    0x3308082008200100, 0x41010500040c020, 0x4012020c04210308, 0x208220a202004080,
    0x111040120082000, 0x6803040141280a00, 0x2101004202410000, 0x8200000041108022,
    0x21082088000, 0x2410204010040, 0x40100400809000, 0x822088220820214,
    0x40808090012004, 0x910224040218c9, 0x402814422015008, 0x90014004842410,
    0x1000042304105, 0x10008830412a00, 0x2520081090008908, 0x40102000a0a60140,
]

# Shift amounts for rooks (how many bits to right-shift the magic result)
ROOK_SHIFTS = [
    52, 53, 53, 53, 53, 53, 53, 52,
    53, 54, 54, 54, 54, 54, 54, 53,
    53, 54, 54, 54, 54, 54, 54, 53,
    53, 54, 54, 54, 54, 54, 54, 53,
    53, 54, 54, 54, 54, 54, 54, 53,
    53, 54, 54, 54, 54, 54, 54, 53,
    53, 54, 54, 54, 54, 54, 54, 53,
    52, 53, 53, 53, 53, 53, 53, 52,
]

# Shift amounts for bishops
BISHOP_SHIFTS = [
    58, 59, 59, 59, 59, 59, 59, 58,
    59, 59, 59, 59, 59, 59, 59, 59,
    59, 59, 57, 57, 57, 57, 59, 59,
    59, 59, 57, 55, 55, 57, 59, 59,
    59, 59, 57, 55, 55, 57, 59, 59,
    59, 59, 57, 57, 57, 57, 59, 59,
    59, 59, 59, 59, 59, 59, 59, 59,
    58, 59, 59, 59, 59, 59, 59, 58,
]


def _generate_rook_mask(square: int) -> int:
    """Generate occupancy mask for rook (excluding edge squares)."""
    rank = square // 8
    file = square % 8
    mask = 0
    
    # North
    for r in range(rank + 1, 7):
        mask |= 1 << (r * 8 + file)
    
    # South
    for r in range(rank - 1, 0, -1):
        mask |= 1 << (r * 8 + file)
    
    # East
    for f in range(file + 1, 7):
        mask |= 1 << (rank * 8 + f)
    
    # West
    for f in range(file - 1, 0, -1):
        mask |= 1 << (rank * 8 + f)
    
    return mask


def _generate_bishop_mask(square: int) -> int:
    """Generate occupancy mask for bishop (excluding edge squares)."""
    rank = square // 8
    file = square % 8
    mask = 0
    
    # NE
    r, f = rank + 1, file + 1
    while r < 7 and f < 7:
        mask |= 1 << (r * 8 + f)
        r += 1
        f += 1
    
    # NW
    r, f = rank + 1, file - 1
    while r < 7 and f > 0:
        mask |= 1 << (r * 8 + f)
        r += 1
        f -= 1
    
    # SE
    r, f = rank - 1, file + 1
    while r > 0 and f < 7:
        mask |= 1 << (r * 8 + f)
        r -= 1
        f += 1
    
    # SW
    r, f = rank - 1, file - 1
    while r > 0 and f > 0:
        mask |= 1 << (r * 8 + f)
        r -= 1
        f -= 1
    
    return mask


def _generate_rook_attacks_slow(square: int, occupied: int) -> int:
    """Generate rook attacks from a square with given occupancy (slow method)."""
    rank = square // 8
    file = square % 8
    attacks = 0
    
    # North
    for r in range(rank + 1, 8):
        attacks |= 1 << (r * 8 + file)
        if occupied & (1 << (r * 8 + file)):
            break
    
    # South
    for r in range(rank - 1, -1, -1):
        attacks |= 1 << (r * 8 + file)
        if occupied & (1 << (r * 8 + file)):
            break
    
    # East
    for f in range(file + 1, 8):
        attacks |= 1 << (rank * 8 + f)
        if occupied & (1 << (rank * 8 + f)):
            break
    
    # West
    for f in range(file - 1, -1, -1):
        attacks |= 1 << (rank * 8 + f)
        if occupied & (1 << (rank * 8 + f)):
            break
    
    return attacks


def _generate_bishop_attacks_slow(square: int, occupied: int) -> int:
    """Generate bishop attacks from a square with given occupancy (slow method)."""
    rank = square // 8
    file = square % 8
    attacks = 0
    
    # NE
    r, f = rank + 1, file + 1
    while r < 8 and f < 8:
        attacks |= 1 << (r * 8 + f)
        if occupied & (1 << (r * 8 + f)):
            break
        r += 1
        f += 1
    
    # NW
    r, f = rank + 1, file - 1
    while r < 8 and f >= 0:
        attacks |= 1 << (r * 8 + f)
        if occupied & (1 << (r * 8 + f)):
            break
        r += 1
        f -= 1
    
    # SE
    r, f = rank - 1, file + 1
    while r >= 0 and f < 8:
        attacks |= 1 << (r * 8 + f)
        if occupied & (1 << (r * 8 + f)):
            break
        r -= 1
        f += 1
    
    # SW
    r, f = rank - 1, file - 1
    while r >= 0 and f >= 0:
        attacks |= 1 << (r * 8 + f)
        if occupied & (1 << (r * 8 + f)):
            break
        r -= 1
        f -= 1
    
    return attacks


def _enumerate_occupancies(mask: int) -> list[int]:
    """Enumerate all possible occupancy variations for a given mask."""
    bits = []
    temp = mask
    while temp:
        bit = temp & -temp
        bits.append(bit)
        temp &= temp - 1
    
    n = len(bits)
    occupancies = []
    for i in range(1 << n):
        occ = 0
        for j in range(n):
            if i & (1 << j):
                occ |= bits[j]
        occupancies.append(occ)
    
    return occupancies


def _init_magic_tables():
    """Initialize magic bitboard lookup tables."""
    rook_tables = []
    bishop_tables = []
    
    for square in range(64):
        # Rook
        mask = _generate_rook_mask(square)
        shift = ROOK_SHIFTS[square]
        magic = ROOK_MAGICS[square]
        table_size = 1 << (64 - shift)
        table = [0] * table_size
        
        occupancies = _enumerate_occupancies(mask)
        for occ in occupancies:
            attacks = _generate_rook_attacks_slow(square, occ)
            index = ((occ * magic) & 0xFFFFFFFFFFFFFFFF) >> shift
            if index < len(table):
                table[index] = attacks
        
        rook_tables.append(table)
        
        # Bishop
        mask = _generate_bishop_mask(square)
        shift = BISHOP_SHIFTS[square]
        magic = BISHOP_MAGICS[square]
        table_size = 1 << (64 - shift)
        table = [0] * table_size
        
        occupancies = _enumerate_occupancies(mask)
        for occ in occupancies:
            attacks = _generate_bishop_attacks_slow(square, occ)
            index = ((occ * magic) & 0xFFFFFFFFFFFFFFFF) >> shift
            if index < len(table):
                table[index] = attacks
        
        bishop_tables.append(table)
    
    return rook_tables, bishop_tables


# Precompute magic tables
ROOK_MASKS = [_generate_rook_mask(sq) for sq in range(64)]
BISHOP_MASKS = [_generate_bishop_mask(sq) for sq in range(64)]
ROOK_TABLES, BISHOP_TABLES = _init_magic_tables()


def get_rook_attacks_magic(square: Square, occupied: int) -> int:
    """Get rook attacks using magic bitboards (O(1) lookup)."""
    sq = square_to_bit(square)
    occ = occupied & ROOK_MASKS[sq]
    index = ((occ * ROOK_MAGICS[sq]) & 0xFFFFFFFFFFFFFFFF) >> ROOK_SHIFTS[sq]
    index = min(index, len(ROOK_TABLES[sq]) - 1)  # Safety check
    return ROOK_TABLES[sq][index]


def get_bishop_attacks_magic(square: Square, occupied: int) -> int:
    """Get bishop attacks using magic bitboards (O(1) lookup)."""
    sq = square_to_bit(square)
    occ = occupied & BISHOP_MASKS[sq]
    index = ((occ * BISHOP_MAGICS[sq]) & 0xFFFFFFFFFFFFFFFF) >> BISHOP_SHIFTS[sq]
    index = min(index, len(BISHOP_TABLES[sq]) - 1)  # Safety check
    return BISHOP_TABLES[sq][index]


def get_queen_attacks_magic(square: Square, occupied: int) -> int:
    """Get queen attacks using magic bitboards (O(1) lookup)."""
    return get_rook_attacks_magic(square, occupied) | get_bishop_attacks_magic(square, occupied)
