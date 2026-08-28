import numpy as np
import chess

from engine.encode import (
    INPUT_PLANES,
    encode_fen,
    encode_board,
    policy_index,
    move_from_policy_index,
)
from engine.board import EngineBoard


START = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
START_BLACK = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1'


def test_encode_shape():
    planes = encode_fen(START)
    assert planes.shape == (INPUT_PLANES, 8, 8)
    assert planes.dtype == np.float32


def test_encode_side_to_move_plane():
    planes = encode_fen(START)
    assert np.allclose(planes[12], 1.0)


def test_encode_flips_for_black():
    white = encode_fen(START)
    black = encode_fen(START_BLACK)
    np.testing.assert_allclose(white[0], black[0])
    np.testing.assert_allclose(white[6], black[6])


def test_policy_index_roundtrip():
    board = EngineBoard()
    move = chess.Move.from_uci('e2e4')
    idx = policy_index(move, flip=False)
    restored = move_from_policy_index(board, idx)
    assert restored == move


def test_encode_is_deterministic():
    a = encode_board(EngineBoard())
    b = encode_board(EngineBoard())
    np.testing.assert_array_equal(a, b)
