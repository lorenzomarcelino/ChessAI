import io

import chess.pgn

from train.dataset import game_passes_filters, iter_pgn_records


def _game(headers, moves='1. e4 e5 2. Nf3 *'):
    text = ''.join(f'[{k} "{v}"]\n' for k, v in headers.items()) + '\n' + moves + '\n'
    return chess.pgn.read_game(io.StringIO(text))


def test_rejects_low_elo():
    game = _game({'WhiteElo': '1500', 'BlackElo': '2400', 'Result': '1-0', 'TimeControl': '600+0'})
    assert not game_passes_filters(game, min_elo=2200)


def test_accepts_high_elo_rapid():
    game = _game({'WhiteElo': '2300', 'BlackElo': '2250', 'Result': '1-0', 'TimeControl': '600+0'})
    assert game_passes_filters(game, min_elo=2200, min_base_time=180)


def test_rejects_bullet_when_min_time_set():
    game = _game({'WhiteElo': '2400', 'BlackElo': '2400', 'Result': '1-0', 'TimeControl': '60+0'})
    assert not game_passes_filters(game, min_elo=2200, min_base_time=180)


def test_iter_pgn_respects_min_elo(tmp_path):
    pgn = tmp_path / 'tiny.pgn'
    pgn.write_text(
        '[WhiteElo "1200"]\n[BlackElo "1200"]\n[Result "1-0"]\n[TimeControl "600+0"]\n\n'
        '1. e4 e5 2. Nf3 Nc6 1-0\n\n'
        '[WhiteElo "2300"]\n[BlackElo "2310"]\n[Result "0-1"]\n[TimeControl "600+0"]\n\n'
        '1. d4 Nf6 2. c4 e6 0-1\n',
        encoding='utf-8',
    )
    records = list(iter_pgn_records(pgn, min_elo=2200, min_ply=0, max_ply=20))
    assert records
    assert records[0]['move'] == 'd2d4'
