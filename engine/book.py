"""Livro de aberturas. Evita erros bobos nos primeiros lances (peso grande vs ~1500)."""

import random

import chess
import chess.polyglot

# Linhas principais. Várias respostas no mesmo ponto = sorteio.
_LINES = (
    'e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7',
    'e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 d2d3',
    'e2e4 e7e5 g1f3 b8c6 d2d4 e5d4 f3d4',
    'e2e4 e7e5 g1f3 g8f6 f3e5 d7d6',
    'e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3',
    'e2e4 c7c5 g1f3 b8c6 d2d4 c5d4 f3d4',
    'e2e4 c7c5 g1f3 e7e6 d2d4 c5d4 f3d4',
    'e2e4 e7e6 d2d4 d7d5 b1c3',
    'e2e4 c7c6 d2d4 d7d5 b1c3',
    'e2e4 d7d5 e4d5 d8d5 b1c3',
    'e2e4 g8f6 e4e5 f6d5',
    'd2d4 d7d5 c2c4 e7e6 b1c3 g8f6',
    'd2d4 d7d5 c2c4 c7c6 g1f3',
    'd2d4 g8f6 c2c4 e7e6 b1c3 f8b4',
    'd2d4 g8f6 c2c4 g7g6 b1c3 f8g7',
    'd2d4 g8f6 g1f3 e7e6 c2c4',
    'd2d4 e7e6 c2c4',
    'g1f3 g8f6 c2c4',
    'g1f3 d7d5 g2g3',
    'c2c4 e7e5 b1c3',
    'c2c4 g8f6 b1c3',
)


def _key(board):
    return chess.polyglot.zobrist_hash(board)


def _build_book():
    book = {}
    for line in _LINES:
        board = chess.Board()
        for uci in line.split():
            moves = book.setdefault(_key(board), [])
            if uci not in moves:
                moves.append(uci)
            move = chess.Move.from_uci(uci)
            if move not in board.legal_moves:
                break
            board.push(move)
    return book


BOOK = _build_book()


def probe(board, rng=None):
    """Devolve UCI do livro ou None."""
    raw = board.raw if hasattr(board, 'raw') else board
    if raw.fullmove_number > 12:
        return None
    options = BOOK.get(_key(raw))
    if not options:
        return None
    legal = {m.uci() for m in raw.legal_moves}
    choices = [uci for uci in options if uci in legal]
    if not choices:
        return None
    rng = rng or random
    return rng.choice(choices)
