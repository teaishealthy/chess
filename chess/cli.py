from typing import Iterable

from .chess import Board
from .models import (
    Color,
    Square,
)


def analysis():  # pragma: no cover
    fen = "r1bqkbnr/pppp1Qpp/8/4p3/1nB1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 1 4"
    piece = Square.from_notation("f7")

    board = Board.from_fen(fen)

    while True:
        moves = list(board.legal_moves(piece) or [])

        print_board(piece, board, moves)
        have_both_kings = (
            board.find_king(Color.WHITE) is not None
            and board.find_king(Color.BLACK) is not None
        )
        if have_both_kings:
            if not board.stalemate:
                print(f"White is in {board.state(Color.WHITE).name}")
                print(f"Black is in {board.state(Color.BLACK).name}")
            else:
                print("Stalemate!")
        else:
            print("One of the kings is missing!")

        move = input("Move: ")
        try:
            if " " in move:
                command, *rest = move.split(" ")
                if command == "h":
                    piece = Square.from_notation(rest[0])
                    continue
                elif command == "f":
                    fen = " ".join(rest)
                    if fen == "s":
                        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
                    board = Board.from_fen(fen)
                    _, piece = next(iter(board))
                    continue
                elif command == "d?":
                    subcommand = rest[0] if rest else ""
                    if subcommand == "p":
                        piece_ = board.squares[piece.rank][piece.file]
                        if piece_ is None:
                            print(f"No piece at {piece.to_notation()}")
                        else:
                            piece_info = (
                                "Piece at "
                                f"{piece.to_notation()} is a {piece_.piece_type.value} "
                                f"with color {piece_.color.name}"
                            )
                            print(piece_info)
                        continue
                    elif subcommand == "b":
                        print(board)
                        continue
                    elif subcommand == "um":
                        if board.last_move is not None:
                            board.undo_move(
                                board.last_move
                            )
                            piece = board.last_move.start
                        continue
                    elif subcommand == "e":
                        exec(" ".join(rest[1:]))
                        continue
                    elif subcommand == "?":
                        print("Commands:")
                        print(" h <square> - highlight piece at square")
                        print(
                            " f <fen> - load board from FEN (use 's' for starting position)"
                        )
                        print(" d? p - display info about highlighted piece")
                        print(" d? b - display board FEN")
                        print(" d? um - undo last move")
                        print(" d? ? - display this help")
                        continue

            start, end = Square.from_notation(move[:2]), Square.from_notation(move[2:])
        except ValueError:
            print("Invalid move!")
            continue
        legal_destinations = list(board.legal_moves(start) or [])
        if end not in legal_destinations:
            print("Illegal move!")
            continue
        board.make_move(Square.from_notation(move[:2]), Square.from_notation(move[2:]))
        piece = Square.from_notation(move[2:])


def print_board(
    piece: Square, board: Board, moves: Iterable[Square]
):  # pragma: no cover
    move_set = {(move.rank, move.file) for move in moves}
    print("\033[0;90;40m  a  b  c  d  e  f  g  h \033[0;37;40m")

    for row_index, row in enumerate(board.squares):
        for square_index, square in enumerate(row):
            if square_index == 0:
                print(f"\033[0;90;40m{8 - row_index}\033[0;37;40m", end="")
            if (row_index, square_index) in move_set:
                print("\033[0;37;42m", end="")
            if (row_index, square_index) == piece:
                print("\033[0;37;44m", end="")
            if square is None:
                print(" .", end=" ")
            else:
                print(
                    f" {square.piece_type.value if square.color == Color.BLACK else square.piece_type.value.upper()}",
                    end=" ",
                )
            if square_index == 7:
                print(f"\033[0;90;40m{8 - row_index}\033[0;37;40m", end="")
            print("\033[0;37;40m", end="")
        print()
    # style the letters as grey
    print("\033[0;90;40m  a  b  c  d  e  f  g  h \033[0;37;40m")


if __name__ == "__main__":  # pragma: no cover
    analysis()
