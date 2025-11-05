import sys

from .chess import Board
from .models import Square


class PerftBoard(Board):
    total_depth: int = 0
    results: dict[str, int] = {}
    """Provides perft (performance test) functionality for a chess board."""

    def perft(self, depth: int) -> int:
        """Calculate the number of possible positions up to a given depth."""
        if depth == 0:
            return 1

        nodes = 0
        for piece, square in self:
            if piece.color != self.to_move:
                continue

            seen: set[Square] = set()
            for target in self.legal_moves(square):
                if target in seen:
                    print(f"??? Duplicate target square {target.to_notation()} for piece at {square.to_notation()}")
                seen.add(target)

                starting_fen = str(self)
                last_move = self.last_move
                move = self.make_move(square, target)
                nodes += (result := self.perft(depth - 1))
                if depth == self.total_depth:
                    notation = f"{square.to_notation()}{target.to_notation()}"
                    assert notation not in self.results, (
                        "Duplicate move notation in perft results", notation
                    )
                    self.results[notation] = result
                    #print(f"{square.to_notation()}{target.to_notation()}: {result}")
                self.undo_move(move)
                self.last_move = last_move
                assert str(self) == starting_fen, (
                    "Board state mismatch after move "
                    f"{square.to_notation()}{target.to_notation()}",
                    self,
                    starting_fen,
                )

        return nodes

def compare_with_stockfish(fen: str, depth: int, results: dict[str, int], total:int) -> None: # pragma: no cover
    import subprocess

    board = PerftBoard.from_fen(fen)
    board.total_depth = depth
    stockfish_results: dict[str, int] = {}

    # Call Stockfish perft
    process = subprocess.Popen(
        ["stockfish"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    stdout, _ = process.communicate(input=f"position fen {fen}\ngo perft {depth}\n")
    stockfish_result = None
    for line in stdout.splitlines():
        if line.startswith("info"):
            continue
        line = line.strip()
        if line.startswith("Nodes searched"):
            parts = line.split()
            stockfish_result = int(parts[-1])
            break
        if line and ":" in line:
            try:
                move, count = line.split(":")
                count_int = int(count.strip())
                stockfish_results[move.strip()] = count_int
            except ValueError:
                pass
        else:
            continue

    if stockfish_result is None:
        print("Failed to get perft result from Stockfish.")
        return

    if total != stockfish_result:
        print(f"Discrepancy in total nodes: Our result = {total}, Stockfish = {stockfish_result}")

    for move, count in results.items():
        stockfish_count = stockfish_results.get(move)
        if stockfish_count is None:
            print(f"Move {move} not found in Stockfish results.")
        elif count != stockfish_count:
            print(f"Discrepancy for move {move}: Our count = {count}, Stockfish count = {stockfish_count}")

    for move in stockfish_results.keys():
        if move not in results:
            print(f"Move {move} found in Stockfish results but not in our results.")

def execute_perft_analysis( fen: str) -> None:  # pragma: no cover
    board = PerftBoard.from_fen(fen)
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    board.total_depth = depth
    result = board.perft(depth)
    print(f"Perft({depth}) = {result}")
    compare_with_stockfish(fen, depth, board.results, result)

if __name__ == "__main__":  # pragma: no cover
    fen = "rnbqkbnr/pppppp1p/8/6p1/7P/8/PPPPPPP1/RNBQKBNR w KQkq g6 0 2"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    execute_perft_analysis(starting_fen)