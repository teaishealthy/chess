import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chess.chess import (
    Board,
    Color,
    Square,
)


def test_is_attacked(benchmark):
    board = Board.from_fen(
        "QQQQQQpk/QQQQQQQp/QQQQQQQQ/QQQQQQQQ/QQQQQQQQ/QQQQQQQQ/QQQQQQQQ/KQQQQQQQ w - - 0 1"
    )
    benchmark(board.in_check, Color.BLACK)