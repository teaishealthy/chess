import sys
import time

from chess.models import BoardProtocol, Square


class PerftMixin(BoardProtocol):
    """Provides perft (performance test) functionality for a chess board."""

    def setup_perft(self, total_depth: int) -> None:
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

def compare_with_stockfish(fen: str, depth: int, results: dict[tuple[Square, Square], int], total:int) -> None: # pragma: no cover
    import subprocess

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

    for (square, target), count in results.items():
        move = f"{square.to_notation()}{target.to_notation()}"
        stockfish_count = stockfish_results.get(move)
        if stockfish_count is None:
            print(f"Move {move} not found in Stockfish results.")
        elif count != stockfish_count:
            print(f"Discrepancy for move {move}: Our count = {count}, Stockfish count = {stockfish_count}")

    for move in stockfish_results:
        sq = (Square.from_notation(move[:2]), Square.from_notation(move[2:]))
        if sq not in results:
            print(f"Move {move} found in Stockfish results but not in our results.")


def execute_perft_analysis( fen: str) -> None:  # pragma: no cover
    from .chess import Board
    start_time = time.perf_counter()
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    board = Board()
    board.setup_perft(depth)
    board.load(fen)

    result = board.perft(depth)
    print(f"Perft({depth}) = {result} in {time.perf_counter() - start_time:.2f} seconds")
    compare_with_stockfish(fen, depth, board.results, result)

if __name__ == "__main__":  # pragma: no cover
    fen = "rnbqkbnr/pppppp1p/8/6p1/7P/8/PPPPPPP1/RNBQKBNR w KQkq g6 0 2"
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    execute_perft_analysis(starting_fen)