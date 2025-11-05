import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chess.chess import Board, BoardState, Color, Move, Piece, PieceType, Square


def make_empty_board() -> Board:
    board = Board()
    board.squares = [[None] * 8 for _ in range(8)]
    return board


def squares_to_coords(moves: Iterable[Square]) -> set[tuple[int, int]]:
    return {(square.rank, square.file) for square in moves}


def place_piece(board: Board, square: Square, color: Color, piece_type: PieceType) -> None:
    board.squares[square.rank][square.file] = Piece(color, piece_type)


def test_rook_moves_respect_blockers():
    board = make_empty_board()
    rook_square = Square(4, 4)
    place_piece(board, rook_square, Color.WHITE, PieceType.ROOK)
    place_piece(board, Square(2, 4), Color.WHITE, PieceType.PAWN)
    place_piece(board, Square(4, 6), Color.BLACK, PieceType.PAWN)

    moves = board.legal_moves(rook_square) or []

    assert squares_to_coords(moves) == {
        (4, 3),
        (4, 2),
        (4, 1),
        (4, 0),
        (4, 5),
        (4, 6),
        (3, 4),
        (5, 4),
        (6, 4),
        (7, 4),
    }


def test_knight_moves_from_corner():
    board = make_empty_board()
    knight_square = Square(0, 1)
    place_piece(board, knight_square, Color.WHITE, PieceType.KNIGHT)

    moves = board.legal_moves(knight_square) or []
    attacks = board.attack_squares(knight_square)

    assert squares_to_coords(moves) == {(2, 0), (2, 2), (1, 3)}
    assert squares_to_coords(attacks) == {(2, 0), (2, 2), (1, 3)}

def test_in_check_detects_rook_attack():
    board = make_empty_board()
    king_square = Square(7, 4)
    attacker_square = Square(0, 4)
    place_piece(board, king_square, Color.WHITE, PieceType.KING)
    place_piece(board, attacker_square, Color.BLACK, PieceType.ROOK)

    result = board.in_check(Color.WHITE)

    assert result is not None
    attacking_square, attacking_piece = result

    assert attacking_square == attacker_square
    assert attacking_piece == Piece(Color.BLACK, PieceType.ROOK)


def test_filter_legal_blocks_pin():
    board = make_empty_board()
    king_square = Square(7, 4)
    defender_square = Square(7, 3)
    attacker_square = Square(7, 0)
    place_piece(board, king_square, Color.WHITE, PieceType.KING)
    place_piece(board, defender_square, Color.WHITE, PieceType.ROOK)
    place_piece(board, attacker_square, Color.BLACK, PieceType.ROOK)

    moves = board.legal_moves(defender_square) or []

    assert squares_to_coords(moves) == {(7, 2), (7, 1), (7, 0)}


def test_bishop_moves_symmetric_blockers():
    board = make_empty_board()
    bishop_square = Square(3, 3)
    place_piece(board, bishop_square, Color.WHITE, PieceType.BISHOP)
    place_piece(board, Square(5, 5), Color.BLACK, PieceType.PAWN)
    place_piece(board, Square(1, 1), Color.WHITE, PieceType.PAWN)

    moves = board.legal_moves(bishop_square) or []
    attacks = board.attack_squares(bishop_square)

    assert (
        squares_to_coords(moves)
        == squares_to_coords(attacks)
        == {
            (4, 4),
            (5, 5),
            (2, 4),
            (1, 5),
            (0, 6),
            (4, 2),
            (5, 1),
            (6, 0),
            (2, 2),
        }
    )


def test_queen_moves_merge_sliding_axes():
    board = make_empty_board()
    queen_square = Square(4, 4)
    place_piece(board, queen_square, Color.WHITE, PieceType.QUEEN)
    place_piece(board, Square(4, 6), Color.BLACK, PieceType.KNIGHT)
    place_piece(board, Square(6, 6), Color.BLACK, PieceType.PAWN)
    place_piece(board, Square(4, 2), Color.WHITE, PieceType.BISHOP)

    moves = board.legal_moves(queen_square) or []
    attacks = board.attack_squares(queen_square)

    assert squares_to_coords(moves) == squares_to_coords(attacks) == {
        (4, 5),
        (4, 6),
        (5, 4),
        (6, 4),
        (7, 4),
        (3, 4),
        (2, 4),
        (1, 4),
        (0, 4),
        (4, 3),
        (5, 5),
        (6, 6),
        (3, 5),
        (2, 6),
        (1, 7),
        (3, 3),
        (2, 2),
        (1, 1),
        (0, 0),
        (5, 3),
        (6, 2),
        (7, 1),
    }


def test_to_notation_round_trip():
    square = Square(2, 6)
    notation = Square.to_notation(square)
    assert notation == "g6"
    assert Square.from_notation(notation) == square

def test_starting_position_fen():
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    board = Board.starting_position()
    assert str(board) == fen

def test_repr():
    starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    board = Board.from_fen(starting_fen)
    assert starting_fen in repr(board)

def test_fen_round_trip():
    fens = [
        "8/8/8/8/8/8/8/8 w - - 0 1",  # empty board
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",  # only kings and rooks
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",  # black to move
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",  # starting position

        "8/8/8/3Pp3/8/8/8/8 w - e6 0 1",  # en passant available
        "8/8/8/8/3pP3/8/8/8 b - e3 0 1",
        "8/8/8/3pP3/8/8/8/8 w - d6 0 1",
        "8/8/8/7p/7P/8/8/8 w - h6 0 1",
        "8/8/8/3p4/4P3/8/8/8 w - d6 0 1",
    ]
    for fen in fens:
        board = Board.from_fen(fen)
        assert str(board) == fen

def test_in_check_returns_none_when_safe():
    board = make_empty_board()
    place_piece(board, Square(7, 4), Color.WHITE, PieceType.KING)
    place_piece(board, Square(0, 0), Color.BLACK, PieceType.ROOK)

    assert board.in_check(Color.WHITE) is None


def test_attacks_include_enemy_king_square_but_moves_exclude():
    board = make_empty_board()
    attacker_square = Square(4, 4)
    king_square = Square(4, 7)
    place_piece(board, attacker_square, Color.WHITE, PieceType.ROOK)
    place_piece(board, king_square, Color.BLACK, PieceType.KING)

    attacks = squares_to_coords(board.attack_squares(attacker_square))
    moves = squares_to_coords(board.legal_moves(attacker_square) or [])

    assert (king_square.rank, king_square.file) in attacks
    assert (king_square.rank, king_square.file) not in moves

def test_pawn_home_row_double_step():
    board = make_empty_board()
    pawn_square = Square(6, 4)
    place_piece(board, pawn_square, Color.WHITE, PieceType.PAWN)

    moves = board.legal_moves(pawn_square) or []

    assert squares_to_coords(moves) == {(5, 4), (4, 4)}

def test_pawn_attacks_are_diagonals_only():
    board = make_empty_board()
    pawn_square = Square(4, 4)
    place_piece(board, pawn_square, Color.WHITE, PieceType.PAWN)

    attacks = squares_to_coords(board.attack_squares(pawn_square))

    assert attacks == {(3, 3), (3, 5)}

def test_pawn_capture_moves_only_diagonals():
    board = make_empty_board()
    pawn_square = Square(4, 4)
    place_piece(board, pawn_square, Color.WHITE, PieceType.PAWN)
    place_piece(board, Square(3, 3), Color.BLACK, PieceType.ROOK)
    place_piece(board, Square(3, 5), Color.WHITE, PieceType.BISHOP)

    moves = board.legal_moves(pawn_square) or []
    assert squares_to_coords(moves) == {(3, 3), (3, 4)}

def test_en_passant_available_against_enemy_pawn():
    board = make_empty_board()
    pawn_square = Square(3, 4)
    place_piece(board, pawn_square, Color.WHITE, PieceType.PAWN)
    last_start = Square(1, 5)
    last_end = Square(3, 5)
    board.squares[last_end.rank][last_end.file] = Piece(Color.BLACK, PieceType.PAWN)
    board.last_move = Move(last_start, last_end, Piece(Color.BLACK, PieceType.PAWN))

    moves = board.legal_moves(pawn_square) or []

    assert Square(2, 5) in moves


def test_en_passant_not_available_against_friendly_pawn():
    board = make_empty_board()
    pawn_square = Square(3, 4)
    place_piece(board, pawn_square, Color.WHITE, PieceType.PAWN)
    last_start = Square(1, 5)
    last_end = Square(3, 5)
    board.squares[last_end.rank][last_end.file] = Piece(Color.WHITE, PieceType.PAWN)
    board.last_move = Move(last_start, last_end, Piece(Color.WHITE, PieceType.PAWN))

    moves = board.legal_moves(pawn_square) or []

    assert Square(2, 5) not in moves

def test_undo_move():
    board = make_empty_board()
    start_square = Square(4, 4)
    end_square = Square(4, 6)
    place_piece(board, start_square, Color.WHITE, PieceType.ROOK)

    old_board = board.copy()
    move = board.make_move(start_square, end_square)
    assert board.squares[end_square.rank][end_square.file] == Piece(Color.WHITE, PieceType.ROOK)
    assert board.squares[start_square.rank][start_square.file] is None

    board.undo_move(move)
    assert board.squares[start_square.rank][start_square.file] == Piece(Color.WHITE, PieceType.ROOK)
    assert board.squares[end_square.rank][end_square.file] is None

    assert str(board.squares) == str(old_board.squares)

def test_undo_en_passant():
    board = make_empty_board()
    white_pawn_square = Square(3, 4)
    black_pawn_start = Square(1, 5)
    black_pawn_end = Square(3, 5)
    place_piece(board, white_pawn_square, Color.WHITE, PieceType.PAWN)
    place_piece(board, black_pawn_end, Color.BLACK, PieceType.PAWN)
    board.last_move = Move(black_pawn_start, black_pawn_end, Piece(Color.BLACK, PieceType.PAWN))

    old_board = board.copy()
    move = board.make_move(white_pawn_square, Square(2, 5))
    assert board.squares[Square(2, 5).rank][Square(2, 5).file] == Piece(Color.WHITE, PieceType.PAWN)
    assert board.squares[white_pawn_square.rank][white_pawn_square.file] is None
    assert board.squares[black_pawn_end.rank][black_pawn_end.file] is None

    board.undo_move(move)
    assert board.squares[white_pawn_square.rank][white_pawn_square.file] == Piece(Color.WHITE, PieceType.PAWN)
    assert board.squares[Square(2, 5).rank][Square(2, 5).file] is None
    assert board.squares[black_pawn_end.rank][black_pawn_end.file] == Piece(Color.BLACK, PieceType.PAWN)

    assert str(board.squares) == str(old_board.squares)

def test_cant_capture_enemy_king():
    board = make_empty_board()
    attacker_square = Square(4, 4)
    king_square = Square(4, 6)
    place_piece(board, attacker_square, Color.WHITE, PieceType.ROOK)
    place_piece(board, king_square, Color.BLACK, PieceType.KING)

    moves = board.legal_moves(attacker_square) or []

    assert king_square not in moves


def test_board_state_normal_when_safe():
    board = make_empty_board()
    white_king = Square(7, 4)
    black_king = Square(0, 4)
    place_piece(board, white_king, Color.WHITE, PieceType.KING)
    place_piece(board, black_king, Color.BLACK, PieceType.KING)

    assert board.state(Color.WHITE) == BoardState.NORMAL


def test_board_state_reports_check():
    board = make_empty_board()
    white_king = Square(7, 4)
    black_king = Square(0, 7)
    attacking_rook = Square(3, 4)
    place_piece(board, white_king, Color.WHITE, PieceType.KING)
    place_piece(board, black_king, Color.BLACK, PieceType.KING)
    place_piece(board, attacking_rook, Color.BLACK, PieceType.ROOK)

    assert board.state(Color.WHITE) == BoardState.CHECK


def test_board_state_reports_checkmate():
    board = make_empty_board()
    white_king = Square(7, 7)
    black_rook = Square(7, 5)
    black_king = Square(5, 7)
    place_piece(board, white_king, Color.WHITE, PieceType.KING)
    place_piece(board, black_rook, Color.BLACK, PieceType.ROOK)
    place_piece(board, black_king, Color.BLACK, PieceType.KING)

    assert board.state(Color.WHITE) == BoardState.CHECKMATE


def test_board_state_reports_stalemate():
    board = make_empty_board()
    black_king = Square(0, 7)
    white_king = Square(2, 6)
    white_queen = Square(1, 5)
    place_piece(board, black_king, Color.BLACK, PieceType.KING)
    place_piece(board, white_king, Color.WHITE, PieceType.KING)
    place_piece(board, white_queen, Color.WHITE, PieceType.QUEEN)

    assert board.state(Color.BLACK) == BoardState.STALEMATE
    assert board.stalemate

def test_board_state_unchanged_during_move_generation():
    board = make_empty_board()
    white_king = Square(7, 4)
    black_rook = Square(7, 5)
    black_king = Square(5, 7)
    place_piece(board, white_king, Color.WHITE, PieceType.KING)
    place_piece(board, black_rook, Color.BLACK, PieceType.ROOK)
    place_piece(board, black_king, Color.BLACK, PieceType.KING)

    last_board_fen = str(board)
    for piece, square in board:
        if piece.color == Color.BLACK:
            for _ in board.legal_moves(square) or []:
                assert str(board) == last_board_fen, "Board modified during move generation"
