import numpy as np
import chess

INPUT_PLANES = 18
POLICY_SIZE = 4096  # from_square * 64 + to_square, no espaço STM

_PIECE_TO_PLANE = {
    chess.PAWN: 0,
    chess.KNIGHT: 1,
    chess.BISHOP: 2,
    chess.ROOK: 3,
    chess.QUEEN: 4,
    chess.KING: 5,
}


def _flip_sq(square, flip):
    return square ^ 56 if flip else square


def encode_board(board):
    """Planos (18, 8, 8) float32. Sempre do ponto de vista de quem joga."""
    raw = board.raw if hasattr(board, 'raw') else board
    flip = raw.turn == chess.BLACK
    planes = np.zeros((INPUT_PLANES, 8, 8), dtype=np.float32)

    for square, piece in raw.piece_map().items():
        sq = _flip_sq(square, flip)
        row, col = divmod(sq, 8)
        plane = _PIECE_TO_PLANE[piece.piece_type]
        ours = piece.color == raw.turn
        planes[plane if ours else plane + 6, 7 - row, col] = 1.0

    planes[12].fill(1.0)

    if raw.has_kingside_castling_rights(raw.turn):
        planes[13].fill(1.0)
    if raw.has_queenside_castling_rights(raw.turn):
        planes[14].fill(1.0)
    if raw.has_kingside_castling_rights(not raw.turn):
        planes[15].fill(1.0)
    if raw.has_queenside_castling_rights(not raw.turn):
        planes[16].fill(1.0)

    if raw.ep_square is not None:
        sq = _flip_sq(raw.ep_square, flip)
        row, col = divmod(sq, 8)
        planes[17, 7 - row, col] = 1.0

    return planes


def encode_fen(fen):
    return encode_board(chess.Board(fen))


def policy_index(move, flip=False):
    frm = _flip_sq(move.from_square, flip)
    to = _flip_sq(move.to_square, flip)
    return frm * 64 + to


def policy_index_for_board(board, move):
    raw = board.raw if hasattr(board, 'raw') else board
    return policy_index(move, flip=raw.turn == chess.BLACK)


def move_from_policy_index(board, index):
    """Converte índice STM de volta para um lance legal, se existir."""
    raw = board.raw if hasattr(board, 'raw') else board
    flip = raw.turn == chess.BLACK
    frm = _flip_sq(index // 64, flip)
    to = _flip_sq(index % 64, flip)
    for move in raw.legal_moves:
        if move.from_square == frm and move.to_square == to:
            return move
    return None
