"""Bitboard-based chess board implementation."""

from __future__ import annotations

from typing import Iterator, Self

from .attacks import (
    get_bishop_attacks,
    get_king_attacks,
    get_knight_attacks,
    get_pawn_attacks,
    get_queen_attacks,
    get_rook_attacks,
)
from .bitboard import (
    RANK_MASKS,
    clear_bit,
    get_bit,
    iter_squares,
    set_bit,
    shift_north,
    shift_south,
    square_to_bit,
)
from .models import (
    BoardState,
    Color,
    KingNotFound,
    Move,
    Piece,
    PieceType,
    Square,
)
from .squares_wrapper import SquaresWrapper


class BitBoard:
    """Chess board representation using bitboards.
    
    Uses 12 bitboards to represent pieces (6 types × 2 colors).
    Each bitboard is a 64-bit integer where each bit represents a square.
    """

    def __init__(self) -> None:
        # Bitboards for each piece type and color
        # Index: [color][piece_type]
        self.pieces: dict[Color, dict[PieceType, int]] = {
            Color.WHITE: {pt: 0 for pt in PieceType},
            Color.BLACK: {pt: 0 for pt in PieceType},
        }
        
        # Fast array access for pieces (avoid dict lookup overhead)
        # Index: [0=WHITE, 1=BLACK][piece_type_index]
        self._piece_bbs: list[list[int]] = [[0] * 6, [0] * 6]
        self._piece_type_list = [PieceType.PAWN, PieceType.KNIGHT, PieceType.BISHOP, 
                                  PieceType.ROOK, PieceType.QUEEN, PieceType.KING]
        
        # Occupancy bitboards (all pieces of a color)
        self.color_occupancy: dict[Color, int] = {
            Color.WHITE: 0,
            Color.BLACK: 0,
        }
        
        # Total occupancy (all pieces)
        self.occupancy: int = 0
        
        # Game state
        self.last_move: Move | None = None
        self.to_move: Color = Color.WHITE
        self.castling_rights: dict[Color, dict[str, bool]] = {
            Color.WHITE: {"K": True, "Q": True},
            Color.BLACK: {"K": True, "Q": True},
        }
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1
        
        # King positions cache
        self._king_positions: dict[Color, Square | None] = {
            Color.WHITE: None,
            Color.BLACK: None,
        }
        
        # Wrapper for backward compatibility with squares[][] access
        self._squares_wrapper = SquaresWrapper(self)
        
        # Lookup table for piece type to index mapping
        self._piece_type_to_idx = {
            PieceType.PAWN: 0,
            PieceType.KNIGHT: 1,
            PieceType.BISHOP: 2,
            PieceType.ROOK: 3,
            PieceType.QUEEN: 4,
            PieceType.KING: 5,
        }
    
    @property
    def squares(self) -> SquaresWrapper:
        """Access bitboards as if they were a 2D array.
        
        This property maintains backward compatibility with the old board representation.
        Returns a wrapper that allows board.squares[rank][file] access.
        """
        return self._squares_wrapper
    
    @squares.setter
    def squares(self, value: list[list[Piece | None]]) -> None:
        """Set bitboards from 2D array for compatibility."""
        # Clear all bitboards
        for color in Color:
            for piece_type in PieceType:
                self.pieces[color][piece_type] = 0
        
        # Set pieces from array
        for rank in range(8):
            for file in range(8):
                piece = value[rank][file]
                if piece is not None:
                    square = Square(rank, file)
                    self.pieces[piece.color][piece.piece_type] = set_bit(
                        self.pieces[piece.color][piece.piece_type], square
                    )
        
        self._sync_piece_bbs()
        self._update_occupancy()
        self._recompute_king_positions()
    
    def _update_occupancy(self) -> None:
        """Update occupancy bitboards."""
        # Use fast array access for better performance
        white_bbs = self._piece_bbs[0]
        black_bbs = self._piece_bbs[1]
        
        self.color_occupancy[Color.WHITE] = (
            white_bbs[0] | white_bbs[1] | white_bbs[2] |
            white_bbs[3] | white_bbs[4] | white_bbs[5]
        )
        self.color_occupancy[Color.BLACK] = (
            black_bbs[0] | black_bbs[1] | black_bbs[2] |
            black_bbs[3] | black_bbs[4] | black_bbs[5]
        )
        
        self.occupancy = self.color_occupancy[Color.WHITE] | self.color_occupancy[Color.BLACK]
    
    def _sync_piece_bbs(self) -> None:
        """Sync fast array with dict representation."""
        for color_idx, color in enumerate([Color.WHITE, Color.BLACK]):
            for pt_idx, pt in enumerate(self._piece_type_list):
                self._piece_bbs[color_idx][pt_idx] = self.pieces[color][pt]
    
    def _recompute_king_positions(self) -> None:
        """Recompute king positions cache."""
        for color in Color:
            king_bb = self.pieces[color][PieceType.KING]
            if king_bb:
                # Get the first (and should be only) king square
                self._king_positions[color] = next(iter_squares(king_bb), None)
            else:
                self._king_positions[color] = None
    
    def _get_piece_at(self, square: Square) -> Piece | None:
        """Get the piece at a square."""
        bit_mask = 1 << square_to_bit(square)
        
        if not (self.occupancy & bit_mask):
            return None
        
        # Check which color (use fast array access)
        if self.color_occupancy[Color.WHITE] & bit_mask:
            color_idx = 0
            color = Color.WHITE
        else:
            color_idx = 1
            color = Color.BLACK
        
        # Check which piece type using fast array
        piece_bbs = self._piece_bbs[color_idx]
        for idx in range(6):
            if piece_bbs[idx] & bit_mask:
                return Piece(color, self._piece_type_list[idx])
        
        return None
    
    def _set_piece(self, square: Square, piece: Piece | None) -> None:
        """Set a piece at a square."""
        bit_mask = 1 << square_to_bit(square)
        
        # Clear any existing piece at this square from all bitboards
        for color_idx in range(2):
            for pt_idx in range(6):
                self._piece_bbs[color_idx][pt_idx] &= ~bit_mask
        
        for color in Color:
            for piece_type in PieceType:
                self.pieces[color][piece_type] &= ~bit_mask
        
        # Set new piece if not None
        if piece is not None:
            color_idx = 0 if piece.color == Color.WHITE else 1
            pt_idx = self._piece_type_to_idx[piece.piece_type]
            self.pieces[piece.color][piece.piece_type] |= bit_mask
            self._piece_bbs[color_idx][pt_idx] |= bit_mask
        
        # Update occupancy efficiently
        self._update_occupancy()
    
    def _set_piece_from_squares(self, rank: int, file: int, piece: Piece | None) -> None:
        """Helper method for squares wrapper to set a piece."""
        self._set_piece(Square(rank, file), piece)
    
    def make_move(self, start: Square, end: Square) -> Move:
        """Make a move on the board."""
        prev_piece = self._get_piece_at(end)
        current_piece = self._get_piece_at(start)
        assert current_piece is not None, "No piece at start square"
        
        captured_square: Square | None = None
        
        start_bit = 1 << square_to_bit(start)
        end_bit = 1 << square_to_bit(end)
        
        # Get fast array indices
        curr_color_idx = 0 if current_piece.color == Color.WHITE else 1
        curr_pt_idx = self._piece_type_to_idx[current_piece.piece_type]
        
        # Handle en passant capture
        if (
            current_piece.piece_type == PieceType.PAWN
            and start.file != end.file
            and prev_piece is None
        ):
            captured_square = Square(start.rank, end.file)
            prev_piece = self._get_piece_at(captured_square)
            if prev_piece:
                cap_bit = 1 << square_to_bit(captured_square)
                prev_color_idx = 0 if prev_piece.color == Color.WHITE else 1
                prev_pt_idx = self._piece_type_to_idx[prev_piece.piece_type]
                self.pieces[prev_piece.color][prev_piece.piece_type] &= ~cap_bit
                self._piece_bbs[prev_color_idx][prev_pt_idx] &= ~cap_bit
        elif prev_piece is not None:
            captured_square = end
            # Remove captured piece
            prev_color_idx = 0 if prev_piece.color == Color.WHITE else 1
            prev_pt_idx = self._piece_type_to_idx[prev_piece.piece_type]
            self.pieces[prev_piece.color][prev_piece.piece_type] &= ~end_bit
            self._piece_bbs[prev_color_idx][prev_pt_idx] &= ~end_bit
        
        # Move the piece using bitboard operations (both dict and fast array)
        self.pieces[current_piece.color][current_piece.piece_type] &= ~start_bit
        self.pieces[current_piece.color][current_piece.piece_type] |= end_bit
        self._piece_bbs[curr_color_idx][curr_pt_idx] &= ~start_bit
        self._piece_bbs[curr_color_idx][curr_pt_idx] |= end_bit
        
        # Update occupancy efficiently
        self._update_occupancy()
        
        # Update king position cache
        if current_piece.piece_type == PieceType.KING:
            self._king_positions[current_piece.color] = end
        if prev_piece is not None and prev_piece.piece_type == PieceType.KING:
            self._king_positions[prev_piece.color] = None
        
        self.last_move = Move(start, end, current_piece, prev_piece, captured_square)
        self.to_move = self.to_move.other
        return self.last_move
    
    def undo_move(self, move: Move) -> None:
        """Undo a move on the board."""
        start_bit = 1 << square_to_bit(move.start)
        end_bit = 1 << square_to_bit(move.end)
        
        # Get fast array indices
        color_idx = 0 if move.piece.color == Color.WHITE else 1
        pt_idx = self._piece_type_to_idx[move.piece.piece_type]
        
        # Move piece back (both dict and fast array)
        self.pieces[move.piece.color][move.piece.piece_type] &= ~end_bit
        self.pieces[move.piece.color][move.piece.piece_type] |= start_bit
        self._piece_bbs[color_idx][pt_idx] &= ~end_bit
        self._piece_bbs[color_idx][pt_idx] |= start_bit
        
        # Handle en passant capture restoration
        if (
            move.piece.piece_type == PieceType.PAWN
            and move.start.file != move.end.file
            and move.captured_square is not None
            and move.captured_square != move.end
        ):
            # Restore captured pawn at captured_square
            if move.captured_piece:
                cap_bit = 1 << square_to_bit(move.captured_square)
                cap_color_idx = 0 if move.captured_piece.color == Color.WHITE else 1
                cap_pt_idx = self._piece_type_to_idx[move.captured_piece.piece_type]
                self.pieces[move.captured_piece.color][move.captured_piece.piece_type] |= cap_bit
                self._piece_bbs[cap_color_idx][cap_pt_idx] |= cap_bit
        elif move.captured_piece is not None:
            # Restore normal capture
            cap_color_idx = 0 if move.captured_piece.color == Color.WHITE else 1
            cap_pt_idx = self._piece_type_to_idx[move.captured_piece.piece_type]
            self.pieces[move.captured_piece.color][move.captured_piece.piece_type] |= end_bit
            self._piece_bbs[cap_color_idx][cap_pt_idx] |= end_bit
        
        # Update occupancy
        self._update_occupancy()
        
        # Update king position cache
        if move.piece.piece_type == PieceType.KING:
            self._king_positions[move.piece.color] = move.start
        if (
            move.captured_piece is not None
            and move.captured_piece.piece_type == PieceType.KING
        ):
            restore_square = move.captured_square or move.end
            self._king_positions[move.captured_piece.color] = restore_square
        
        self.last_move = None
        self.to_move = self.to_move.other
    
    def find_king(self, color: Color) -> Square | None:
        """Find the king of the given color."""
        king_square = self._king_positions[color]
        if king_square is not None:
            return king_square
        self._recompute_king_positions()
        return self._king_positions[color]
    
    def __iter__(self) -> Iterator[tuple[Piece, Square]]:
        """Iterate over all pieces on the board."""
        for color in Color:
            for piece_type in PieceType:
                bb = self.pieces[color][piece_type]
                for square in iter_squares(bb):
                    yield Piece(color, piece_type), square
    
    def copy(self) -> Self:
        """Create a copy of the board."""
        from .bitboard_fen import BitBoardFenMixin
        
        # Create a new board with FEN support
        board = type(self)()
        if isinstance(self, BitBoardFenMixin):
            board = type(self).from_fen(str(self))
            board.last_move = self.last_move
        return board
    
    def __copy__(self) -> Self:
        return self.copy()
    
    def __str__(self) -> str:
        from .bitboard_fen import BitBoardFenMixin
        
        if isinstance(self, BitBoardFenMixin):
            return self.dump()
        return repr(self)
    
    def __repr__(self) -> str:
        return f"BitBoard({self})"
    
    def legal_moves(self, square: Square) -> Iterator[Square]:
        """Generate legal moves for a piece at a square."""
        from .bitboard_movegen import BitBoardMoveGenMixin
        
        if isinstance(self, BitBoardMoveGenMixin):
            return self.legal_moves(square)
        return iter([])
    
    def in_check(self, color: Color) -> tuple[Square, Piece] | None:
        """Check if the given color is in check."""
        from .bitboard_movegen import BitBoardMoveGenMixin
        
        if isinstance(self, BitBoardMoveGenMixin):
            return self.in_check(color)
        return None
    
    def state(self, color: Color) -> BoardState:
        """Determine the state of the board for the given color."""
        has_legal_move = False
        for piece, sq in self:
            if piece.color == color and self.has_any_legal_move(sq):
                has_legal_move = True
                break
        
        in_check = self.in_check(color) is not None
        if has_legal_move:
            return BoardState.CHECK if in_check else BoardState.NORMAL
        
        return BoardState.CHECKMATE if in_check else BoardState.STALEMATE
    
    @property
    def stalemate(self) -> bool:
        """Check if the board is in stalemate."""
        return (
            self.state(Color.WHITE) == BoardState.STALEMATE
            or self.state(Color.BLACK) == BoardState.STALEMATE
        )
    
    def has_any_legal_move(self, square: Square) -> bool:
        """Check if a piece has any legal moves."""
        return next(self.legal_moves(square), None) is not None
    
    def attack_squares(self, square: Square) -> Iterator[Square]:
        """Get attack squares for a piece."""
        from .bitboard_movegen import BitBoardMoveGenMixin
        
        if isinstance(self, BitBoardMoveGenMixin):
            return self.attack_squares(square)
        return iter([])
    
    def is_attacked(self, square: Square, by_color: Color) -> tuple[Square, Piece] | None:
        """Check if a square is attacked by a given color."""
        from .bitboard_movegen import BitBoardMoveGenMixin
        
        if isinstance(self, BitBoardMoveGenMixin):
            return self.is_attacked(square, by_color)
        return None
