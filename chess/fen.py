from .models import BoardProtocol, Color, Move, Piece, PieceType, Square


class FenMixin(BoardProtocol):
    """Parse and serialize FEN strings."""
    def load(self, fen: str) -> None:
        (
            positions,
            to_move,
            castling_rights,
            en_passant_target,
            halfmove_clock,
            fullmove_number,
        ) = fen.split(" ")

        rank = 0
        file = 0
        for char in positions:
            if char == "/":
                rank += 1
                file = 0
            elif char.isnumeric():
                file += int(char)
            else:
                color = Color.WHITE if char.isupper() else Color.BLACK
                piece_type = PieceType(char.lower())
                self.squares[rank][file] = Piece(color, piece_type)
                file += 1

        self.to_move = Color.WHITE if to_move == "w" else Color.BLACK
        self.castling_rights = {
            Color.WHITE: {"K": "K" in castling_rights, "Q": "Q" in castling_rights},
            Color.BLACK: {"K": "k" in castling_rights, "Q": "q" in castling_rights},
        }

        self.last_move = None
        if en_passant_target != "-":
            ep_square = Square.from_notation(en_passant_target)
            direction = self.to_move.direction
            pawn_rank = ep_square.rank - direction
            pawn_start = Square(pawn_rank + direction * 2, ep_square.file)
            pawn_end = Square(pawn_rank, ep_square.file)
            pawn_piece = self.squares[pawn_end.rank][pawn_end.file]
            assert (
                pawn_piece is not None
                and pawn_piece.piece_type == PieceType.PAWN
                and pawn_piece.color == self.to_move.other
            ), "Invalid en passant target in FEN"
            self.last_move = Move(
                start=pawn_start,
                end=Square(pawn_rank, ep_square.file),
                piece=pawn_piece,
            )

        self.halfmove_clock = int(halfmove_clock)
        self.fullmove_number = int(fullmove_number)

    def dump(self: BoardProtocol) -> str:
        fen_ranks: list[str] = []
        for rank in self.squares:
            fen_rank = ""
            empty_count = 0
            for square in rank:
                if square is None:
                    empty_count += 1
                else:
                    if empty_count:
                        fen_rank += str(empty_count)
                        empty_count = 0
                    fen_rank += (
                        square.piece_type.value
                        if square.color == Color.BLACK
                        else square.piece_type.value.upper()
                    )
            if empty_count:
                fen_rank += str(empty_count)
            fen_ranks.append(fen_rank)

        positions = "/".join(fen_ranks)
        to_move_char = "w" if self.to_move == Color.WHITE else "b"

        castling_chars = ""
        if self.castling_rights[Color.WHITE]["K"]:
            castling_chars += "K"
        if self.castling_rights[Color.WHITE]["Q"]:
            castling_chars += "Q"
        if self.castling_rights[Color.BLACK]["K"]:
            castling_chars += "k"
        if self.castling_rights[Color.BLACK]["Q"]:
            castling_chars += "q"
        castling_chars = castling_chars or "-"

        en_passant_char = "-"
        if self.last_move is not None and self.last_move.en_passant_target:
            ep_rank = self.last_move.end.rank - self.last_move.piece.color.direction
            ep_file = self.last_move.end.file
            en_passant_char = Square(ep_rank, ep_file).to_notation()

        return (
            f"{positions} {to_move_char} {castling_chars} "
            f"{en_passant_char} {self.halfmove_clock} {self.fullmove_number}"
        )

    @classmethod
    def from_fen(cls, fen: str):
        """Create a board from a FEN string"""
        board = cls()
        board.load(fen)
        return board

    @classmethod
    def starting_position(cls):
        """Create the starting position for a chess game"""
        return cls.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
