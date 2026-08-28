from engine.api import think
from engine.board import EngineBoard
from engine.skill import get_skill, pick_from_scores, SKILL_ORDER
from engine.search import Searcher


def test_skill_names():
    assert len(SKILL_ORDER) == 5
    assert get_skill(0).name == 'iniciante'
    assert get_skill('mestre').depth >= get_skill('iniciante').depth


def test_think_with_skill_returns_legal_move():
    board = EngineBoard()
    move = think(skill='iniciante')
    assert move in board.legal_moves()


def test_beginner_is_shallower_than_medium():
    board = EngineBoard()
    easy = Searcher()
    mid = Searcher()
    easy.search(board, depth=get_skill('iniciante').depth, nodes=get_skill('iniciante').nodes)
    mid.search(board, depth=get_skill('medio').depth, nodes=get_skill('medio').nodes)
    assert mid.completed_depth >= easy.completed_depth


def test_pick_from_scores_prefers_best_without_alt():
    class Move:
        def __init__(self, name):
            self.name = name

    best = Move('best')
    other = Move('other')
    assert pick_from_scores([(10, best), (1, other)], alt_move_p=0) is best
