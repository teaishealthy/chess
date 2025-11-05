import shutil
import subprocess

import pytest

from chess.chess import Board


@pytest.fixture(scope="module")
def stockfish_path() -> str:
	path = shutil.which("stockfish")
	if path is None:
		pytest.skip("Stockfish engine not available on PATH")
	return path


def run_stockfish_perft(stockfish_path: str, fen: str, depth: int) -> tuple[int, dict[str, int]]:
	process = subprocess.Popen(
		[stockfish_path],
		stdin=subprocess.PIPE,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		text=True,
	)

	try:
		stdout, stderr = process.communicate(
			input=f"uci\nisready\nposition fen {fen}\ngo perft {depth}\nquit\n",
			timeout=30,
		)
	except subprocess.TimeoutExpired:
		process.kill()
		raise

	if process.returncode not in (0, None):
		raise RuntimeError(f"Stockfish exited with code {process.returncode}: {stderr.strip()}")

	root_counts: dict[str, int] = {}
	total_nodes: int | None = None

	for raw_line in stdout.splitlines():
		line = raw_line.strip()
		if not line:
			continue
		if line.lower().startswith("stockfish") or line.startswith("info"):
			continue
		if "nodes searched" in line.lower():
			try:
				total_nodes = int(line.split()[-1])
			except (IndexError, ValueError) as error:
				raise AssertionError(f"Unable to parse Stockfish total from line: {line}") from error
			continue
		if ":" not in line:
			continue
		move_part, count_part = line.split(":", 1)
		move = move_part.strip()
		try:
			root_counts[move] = int(count_part.strip())
		except ValueError as error:
			raise AssertionError(f"Unable to parse Stockfish entry: {line}") from error

	if total_nodes is None:
		raise AssertionError(f"Stockfish output missing total nodes. Output was:\n{stdout}")

	return total_nodes, root_counts


def run_engine_perft(fen: str, depth: int) -> tuple[int, dict[str, int]]:
    board = Board()
    board.load(fen)
    board.total_depth = depth
    board.results = {}
    total = board.perft(depth)
    results = {
        f"{start.to_notation()}{end.to_notation()}": count
        for (start, end), count in board.results.items()
    }
    return total, results

def test_benchmark_perft(benchmark) -> None:
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    board = Board()
    board.load(starting_fen)
    board.setup_perft(2)

    benchmark(board.perft, 2)

@pytest.mark.parametrize("depth", [1, 2, 3, 4])
def test_perft_matches_stockfish(stockfish_path: str, depth: int) -> None:
	starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
	stockfish_total, stockfish_roots = run_stockfish_perft(stockfish_path, starting_fen, depth)
	engine_total, engine_roots = run_engine_perft(starting_fen, depth)

	assert engine_total == stockfish_total, (
		f"Total nodes mismatch at depth {depth}: engine={engine_total}, stockfish={stockfish_total}"
	)
	assert engine_roots == stockfish_roots, (
		f"Root move breakdown mismatch at depth {depth}"
	)
