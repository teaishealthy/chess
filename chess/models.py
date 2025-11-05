from __future__ import annotations

from enum import Enum, auto
from typing import Iterable, Iterator, NamedTuple, Protocol


class Color(Enum):
    WHITE = 1
    BLACK = 2

    @property
    def other(self) -> Color:
        """Get the opposite color"""
        return Color.BLACK if self == Color.WHITE else Color.WHITE

    @property
    def direction(self) -> int:
        """Get the forward direction for the color: -1 for white, 1 for black"""
        return -1 if self == Color.WHITE else 1


class PieceType(Enum):
    PAWN = "p"
    ROOK = "r"
    KNIGHT = "n"
    BISHOP = "b"
    QUEEN = "q"
    KING = "k"


class BoardState(Enum):
    CHECKMATE = auto()
    CHECK = auto()
    STALEMATE = auto()
    NORMAL = auto()


class Piece(NamedTuple):
    color: Color
    piece_type: PieceType


class KingNotFound(Exception):
    pass


class Square(NamedTuple):
    rank: int
    file: int

    def to_notation(self) -> str:
        return chr(self.file + 97) + str(8 - self.rank)

    @staticmethod
    def from_notation(notation: str) -> Square:
        file = ord(notation[0]) - 97
        rank = 8 - int(notation[1])
        return Square(rank, file)

    def __repr__(self) -> str:
        return f"Square({self.to_notation()})"

    def check_limits(self) -> bool:
        return 0 <= self.rank < 8 and 0 <= self.file < 8


class Move(NamedTuple):
    start: Square
    end: Square
    piece: Piece
    captured_piece: Piece | None = None
    captured_square: Square | None = None

    @property
    def en_passant_target(self) -> bool:
        # Check if this pawn move can be an en passant target
        if self.piece.piece_type != PieceType.PAWN:
            return False
        if abs(self.start.rank - self.end.rank) == 2:
            return True
        return False


Direction = tuple[int, int]


ROOK_DIRECTIONS: Iterable[Direction] = ((1, 0), (-1, 0), (0, 1), (0, -1))
BISHOP_DIRECTIONS: Iterable[Direction] = ((1, 1), (1, -1), (-1, 1), (-1, -1))
QUEEN_DIRECTIONS: Iterable[Direction] = ROOK_DIRECTIONS + BISHOP_DIRECTIONS

KING_OFFSETS: Iterable[Direction] = (
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
    (0, -1),
    (1, -1),
)

KNIGHT_OFFSETS: Iterable[Direction] = (
    (1, 2),
    (2, 1),
    (-1, 2),
    (-2, 1),
    (1, -2),
    (2, -1),
    (-1, -2),
    (-2, -1),
)


class BoardProtocol(Protocol):
    squares: list[list[Piece | None]]
    last_move: Move | None
    to_move: Color
    castling_rights: dict[Color, dict[str, bool]]
    halfmove_clock: int
    fullmove_number: int

    def make_move(self, start: Square, end: Square) -> Move: ...

    def undo_move(self, move: Move) -> None: ...

    def in_check(self, color: Color) -> tuple[Square, Piece] | None: ...

    def legal_moves(self, square: Square) -> Iterable[Square]: ...

    def __iter__(self) -> Iterator[tuple[Piece, Square]]: ...