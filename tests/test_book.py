from engine.board import EngineBoard
from engine.book import probe, BOOK


def test_book_has_startpos():
    move = probe(EngineBoard())
    assert move in EngineBoard().legal_moves()
    assert len(BOOK) > 20


def test_book_empty_in_random_middle_game():
    board = EngineBoard.from_fen('4k3/8/8/8/8/8/4P3/4K3 w - - 0 40')
    assert probe(board) is None
