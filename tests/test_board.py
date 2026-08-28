from pathlib import Path

import chess

from engine.board import EngineBoard


ENGINE_DIR = Path(__file__).resolve().parents[1] / 'engine'

START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
KIWIPETE = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'


def test_engine_has_no_pygame():
    for path in ENGINE_DIR.glob('*.py'):
        text = path.read_text(encoding='utf-8')
        assert 'pygame' not in text, f'{path.name} importa pygame'


def test_startpos_legal_move_count():
    board = EngineBoard()
    assert len(board.legal_moves()) == 20
    assert board.turn == 'white'


def test_perft_startpos():
    board = EngineBoard()
    assert board.perft(1) == 20
    assert board.perft(2) == 400
    assert board.perft(3) == 8902


def test_perft_kiwipete():
    board = EngineBoard.from_fen(KIWIPETE)
    assert board.perft(1) == 48
    assert board.perft(2) == 2039


def test_from_fen_to_fen_roundtrip():
    board = EngineBoard.from_fen(START_FEN)
    assert board.to_fen().startswith('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')


def test_push_pop_restores_position():
    board = EngineBoard()
    fen = board.to_fen()
    board.push('e2e4')
    assert board.turn == 'black'
    board.pop()
    assert board.to_fen() == fen
    assert board.turn == 'white'


def test_castling_white_both_sides():
    board = EngineBoard.from_fen('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1')
    moves = set(board.legal_moves())
    assert 'e1g1' in moves
    assert 'e1c1' in moves
    board.push('e1g1')
    assert board.raw.piece_at(chess.G1).symbol() == 'K'
    assert board.raw.piece_at(chess.F1).symbol() == 'R'


def test_en_passant_is_legal():
    board = EngineBoard.from_fen('rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3')
    assert 'e5f6' in board.legal_moves()
    board.push('e5f6')
    assert board.raw.piece_at(chess.F6) is not None
    assert board.raw.piece_at(chess.F5) is None


def test_promotion():
    board = EngineBoard.from_fen('8/4P3/8/8/8/8/8/4K1k1 w - - 0 1')
    moves = board.legal_moves()
    assert 'e7e8q' in moves
    board.push('e7e8q')
    assert board.raw.piece_at(chess.E8).symbol() == 'Q'


def test_checkmate_detected():
    board = EngineBoard.from_fen('6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1')
    board.push('e1e8')
    assert board.is_checkmate
    assert board.is_game_over


def test_stalemate_detected():
    board = EngineBoard.from_fen('7k/5Q2/6K1/8/8/8/8/8 b - - 0 1')
    assert board.is_stalemate
    assert board.is_game_over
    assert not board.is_checkmate
