import time

from engine.api import think
from engine.board import EngineBoard
from engine.evaluate import evaluate
from engine.search import Searcher


MATE_IN_ONE = '6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1'
SCHOLARS_MATE = 'rnbqkbnr/pppp1ppp/8/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 0 4'


def test_evaluate_startpos_is_symmetric():
    board = EngineBoard()
    assert evaluate(board) == 0


def test_evaluate_white_ahead_in_material():
    board = EngineBoard.from_fen('4k3/8/8/8/8/8/8/4K2Q w - - 0 1')
    assert evaluate(board) > 800


def test_mate_in_one_depth_1():
    assert think(MATE_IN_ONE, depth=1) == 'e1e8'


def test_mate_in_one_depth_2():
    assert think(MATE_IN_ONE, depth=2) == 'e1e8'


def test_scholars_mate_in_one():
    move = think(SCHOLARS_MATE, depth=2)
    assert move == 'f3f7'


def test_think_startpos_returns_legal_move():
    board = EngineBoard()
    move = think(depth=3)
    assert move in board.legal_moves()


def test_think_respects_node_limit():
    searcher = Searcher()
    board = EngineBoard()
    move = searcher.search(board, depth=8, nodes=200)
    assert move in board.legal_moves()
    assert searcher.nodes <= 400


def test_think_respects_time_limit():
    started = time.perf_counter()
    move = think(depth=12, time_ms=80)
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert move is not None
    assert elapsed_ms < 1500


def test_selfplay_short_game_completes():
    board = EngineBoard()
    for _ in range(8):
        if board.is_game_over:
            break
        move = think(board.to_fen(), depth=3)
        assert move in board.legal_moves()
        board.push(move)
    assert not board.is_game_over or board.is_checkmate or board.is_stalemate


def test_network_is_called_once_per_search(monkeypatch):
    import numpy as np

    from engine.encode import POLICY_SIZE

    calls = {'n': 0}

    def fake_infer(board):
        calls['n'] += 1
        return np.zeros(POLICY_SIZE, dtype=np.float32), 0

    monkeypatch.setattr('engine.nn_eval.infer', fake_infer)
    searcher = Searcher()
    board = EngineBoard()
    move = searcher.search(board, depth=3, use_network=True)
    assert move in board.legal_moves()
    assert calls['n'] == 1


def test_nodes_per_second_baseline():
    searcher = Searcher()
    board = EngineBoard()
    started = time.perf_counter()
    searcher.search(board, depth=4)
    elapsed = time.perf_counter() - started
    nps = searcher.nodes / max(elapsed, 1e-6)
    assert searcher.completed_depth >= 4
    assert nps > 50
