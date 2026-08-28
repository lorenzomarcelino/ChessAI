import json
import random
from pathlib import Path

import chess
import chess.pgn
import numpy as np
from torch.utils.data import IterableDataset, Dataset

from engine.encode import encode_board, policy_index_for_board


def result_to_score(result_str):
    if result_str == '1-0':
        return 1.0
    if result_str == '0-1':
        return -1.0
    return 0.0


def game_passes_filters(game, min_elo=0, min_base_time=0):
    result = game.headers.get('Result', '*')
    if result not in ('1-0', '0-1', '1/2-1/2'):
        return False
    try:
        white_elo = int(game.headers.get('WhiteElo', 0) or 0)
        black_elo = int(game.headers.get('BlackElo', 0) or 0)
    except ValueError:
        return False
    if min_elo and min(white_elo, black_elo) < min_elo:
        return False
    if min_base_time:
        clock = game.headers.get('TimeControl', '')
        if '+' in clock:
            base = clock.split('+')[0]
        else:
            base = clock
        try:
            if int(base) < min_base_time:
                return False
        except ValueError:
            return False
    return True


def records_from_game(game, min_ply=0, max_ply=120):
    result = result_to_score(game.headers.get('Result', '*'))
    board = game.board()
    ply = 0
    for move in game.mainline_moves():
        if min_ply <= ply <= max_ply:
            stm_result = result if board.turn == chess.WHITE else -result
            yield {
                'fen': board.fen(),
                'move': move.uci(),
                'value': stm_result,
            }
        board.push(move)
        ply += 1
        if ply > max_ply:
            break


def open_pgn(path):
    path = Path(path)
    if path.suffix == '.zst' or str(path).endswith('.pgn.zst'):
        import zstandard as zstd
        return zstd.open(path, 'rt', encoding='utf-8', errors='replace')
    return open(path, encoding='utf-8', errors='replace')


def iter_pgn_records(path, max_games=None, min_elo=0, min_ply=0, max_ply=120, min_base_time=0):
    with open_pgn(path) as handle:
        count = 0
        while True:
            game = chess.pgn.read_game(handle)
            if game is None:
                break
            if not game_passes_filters(game, min_elo=min_elo, min_base_time=min_base_time):
                continue
            yield from records_from_game(game, min_ply=min_ply, max_ply=max_ply)
            count += 1
            if max_games is not None and count >= max_games:
                break


def load_pgn(path, max_games=None, min_elo=0):
    return list(iter_pgn_records(path, max_games=max_games, min_elo=min_elo))


def load_jsonl(path):
    records = []
    with open(path, encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def sample_jsonl(path, k, seed=0):
    """Reservatório: lê o arquivo uma vez e guarda no máximo k linhas."""
    rng = random.Random(seed)
    sample = []
    seen = 0
    with open(path, encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if seen < k:
                sample.append(line)
            else:
                j = rng.randint(0, seen)
                if j < k:
                    sample[j] = line
            seen += 1
    records = [json.loads(item) for item in sample]
    return records, seen


def write_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        for record in records:
            handle.write(json.dumps(record) + '\n')


def encode_record(record):
    board = chess.Board(record['fen'])
    planes = encode_board(board)
    move = chess.Move.from_uci(record['move'])
    policy = policy_index_for_board(board, move)
    value = float(record['value'])
    return planes, policy, value


class PositionDataset(Dataset):
    def __init__(self, records):
        self.records = records

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        planes, policy, value = encode_record(self.records[idx])
        return planes.astype(np.float32), np.int64(policy), np.float32(value)


class JsonlIterableDataset(IterableDataset):
    """Lê JSONL linha a linha — serve para dumps grandes sem estourar RAM."""

    def __init__(self, path):
        self.path = Path(path)

    def __iter__(self):
        with open(self.path, encoding='utf-8') as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                planes, policy, value = encode_record(json.loads(line))
                yield planes.astype(np.float32), np.int64(policy), np.float32(value)
