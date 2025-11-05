"""Perft (performance test) functionality for bitboard-based board."""

from __future__ import annotations

from .bitboard_board import BitBoard
from .models import Square


class BitBoardPerftMixin(BitBoard):
    """Provides perft (performance test) functionality for bitboard-based board."""

    def setup_perft(self, total_depth: int) -> None:
        """Set up perft tracking."""
        self.total_depth = total_depth
        self.results: dict[tuple[Square, Square], int] = {}

    def perft(self, depth: int) -> int:
        """Calculate the number of possible positions up to a given depth."""
        if depth == 0:
            return 1

        nodes = 0
        for piece, square in self:
            if piece.color != self.to_move:
                continue

            for target in self.legal_moves(square):
                last_move = self.last_move
                move = self.make_move(square, target)
                nodes += (result := self.perft(depth - 1))

                if depth == self.total_depth:
                    self.results[(square, target)] = result

                self.undo_move(move)
                self.last_move = last_move
        return nodes
