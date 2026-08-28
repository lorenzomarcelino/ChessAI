"""Gera partidas engine vs engine (Fase 3.3)."""

import argparse
import random

from engine.board import EngineBoard
from engine.api import think
from train.dataset import write_jsonl


def play_game(depth=2, max_plies=80, seed=None):
    rng = random.Random(seed)
    board = EngineBoard()
    records = []
    while not board.is_game_over and len(records) < max_plies:
        fen = board.to_fen()
        legal = board.legal_moves()
        if rng.random() < 0.08:
            move = rng.choice(legal)
        else:
            move = think(fen, depth=depth)
        if move is None:
            break
        records.append({'fen': fen, 'move': move, 'value': 0.0})
        board.push(move)

    if board.is_checkmate:
        winner_was_black = board.turn == 'white'
        game_result = -1.0 if winner_was_black else 1.0
    else:
        game_result = 0.0

    labeled = []
    temp = EngineBoard()
    for record in records:
        stm_white = temp.turn == 'white'
        record = dict(record)
        record['value'] = game_result if stm_white else -game_result
        labeled.append(record)
        temp.push(record['move'])
    return labeled


def main():
    parser = argparse.ArgumentParser(description='Self-play da engine clássica.')
    parser.add_argument('--games', type=int, default=20)
    parser.add_argument('--depth', type=int, default=2)
    parser.add_argument('--out', default='data/selfplay.jsonl')
    args = parser.parse_args()

    all_records = []
    for i in range(args.games):
        all_records.extend(play_game(depth=args.depth, seed=i))
        print(f'partida {i + 1}/{args.games} ({len(all_records)} posições)')
    write_jsonl(args.out, all_records)
    print(f'gravado {args.out}')


if __name__ == '__main__':
    main()
