import chess
import random

PAWN = 100
KNIGHT = 320
BISHOP = 330
ROOK = 500
QUEEN = 900

PIECE_VALUES = {
    chess.PAWN: PAWN,
    chess.KNIGHT: KNIGHT,
    chess.BISHOP: BISHOP,
    chess.ROOK: ROOK,
    chess.QUEEN: QUEEN,
    chess.KING: 0,
}

# Tabelas com a8 no índice 0 (visão das brancas). Brancas: sq ^ 56; pretas: sq.
_PAWN_PST = (
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0,
)

_KNIGHT_PST = (
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
)

_BISHOP_PST = (
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
)

_ROOK_PST = (
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
)

_QUEEN_PST = (
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
)

_KING_MG_PST = (
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
)

_KING_EG_PST = (
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50,
)

_PST = {
    chess.PAWN: _PAWN_PST,
    chess.KNIGHT: _KNIGHT_PST,
    chess.BISHOP: _BISHOP_PST,
    chess.ROOK: _ROOK_PST,
    chess.QUEEN: _QUEEN_PST,
}

_PHASE_WEIGHT = {
    chess.KNIGHT: 1,
    chess.BISHOP: 1,
    chess.ROOK: 2,
    chess.QUEEN: 4,
    chess.PAWN: 0,
    chess.KING: 0,
}
_PHASE_MAX = 24


def _pst(piece_type, square, color, table):
    index = square ^ 56 if color == chess.WHITE else square
    return table[index]


def classical_evaluate(board):
    """Centipeões artesanais do ponto de vista de quem joga."""
    raw = board.raw if hasattr(board, 'raw') else board
    mg = 0
    eg = 0
    phase = 0
    bishops = {chess.WHITE: 0, chess.BLACK: 0}

    for square, piece in raw.piece_map().items():
        sign = 1 if piece.color == chess.WHITE else -1
        value = PIECE_VALUES[piece.piece_type]
        if piece.piece_type == chess.KING:
            mg += sign * _pst(piece.piece_type, square, piece.color, _KING_MG_PST)
            eg += sign * _pst(piece.piece_type, square, piece.color, _KING_EG_PST)
        else:
            bonus = _pst(piece.piece_type, square, piece.color, _PST[piece.piece_type])
            mg += sign * (value + bonus)
            eg += sign * (value + bonus)
        phase += _PHASE_WEIGHT[piece.piece_type]
        if piece.piece_type == chess.BISHOP:
            bishops[piece.color] += 1

    if bishops[chess.WHITE] >= 2:
        mg += 30
        eg += 40
    if bishops[chess.BLACK] >= 2:
        mg -= 30
        eg -= 40

    phase = min(phase, _PHASE_MAX)
    score = (mg * phase + eg * (_PHASE_MAX - phase)) // _PHASE_MAX
    return score if raw.turn == chess.WHITE else -score


def evaluate(board, noise_std=0, use_network=False):
    """Centipeões do ponto de vista de quem joga.

    A busca usa eval clássica nas folhas. `use_network=True` fica para
    experimentos; a CNN de política entra só na raiz (`search.py`).
    """
    score = None
    if use_network:
        from engine import nn_eval
        score = nn_eval.value_cp(board)
    if score is None:
        score = classical_evaluate(board)
    if noise_std:
        score += int(random.gauss(0, noise_std))
    return score
