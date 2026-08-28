"""Relabel de value com a busca da própria engine (Fase 3.2)."""

import argparse
import math

from engine.board import EngineBoard
from engine.search import Searcher
from train.dataset import load_jsonl, write_jsonl


def score_to_value(cp):
    return math.tanh(cp / 400.0)


def distill_records(records, depth=4):
    searcher = Searcher()
    out = []
    for i, record in enumerate(records):
        board = EngineBoard.from_fen(record['fen'])
        if board.is_game_over:
            continue
        searcher.search(board, depth=depth)
        raw = board.raw
        key_move = None
        value_cp = 0
        if searcher.root_move is not None:
            key_move = searcher.root_move
        # Usa a eval clássica da posição após o melhor lance como proxy se não houver score
        raw.push(key_move or list(raw.legal_moves)[0])
        from engine.evaluate import classical_evaluate
        value_cp = -classical_evaluate(raw)
        raw.pop()
        updated = dict(record)
        updated['value'] = score_to_value(value_cp)
        if key_move is not None:
            updated['move'] = key_move.uci()
        out.append(updated)
        if (i + 1) % 25 == 0:
            print(f'{i + 1}/{len(records)}')
    return out


def main():
    parser = argparse.ArgumentParser(description='Destila alvos de value com a busca.')
    parser.add_argument('--data', required=True)
    parser.add_argument('--out', default='data/distilled.jsonl')
    parser.add_argument('--depth', type=int, default=3)
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()

    records = load_jsonl(args.data)
    if args.limit:
        records = records[: args.limit]
    distilled = distill_records(records, depth=args.depth)
    write_jsonl(args.out, distilled)
    print(f'gravado {args.out} ({len(distilled)} posições)')


if __name__ == '__main__':
    main()
