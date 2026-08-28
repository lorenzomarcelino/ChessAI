"""Baixa / filtra PGN Lichess (Elo alto) e grava JSONL para o treino."""

import argparse
import json
import random
import sys
import urllib.request
from pathlib import Path

from train.dataset import iter_pgn_records

LICHESS_MONTH = 'https://database.lichess.org/standard/lichess_db_standard_rated_{month}.pgn.zst'


def download(month, dest):
    url = LICHESS_MONTH.format(month=month)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f'baixando {url}')
    print('arquivo grande (vários GB). deixe rodar.')
    urllib.request.urlretrieve(url, dest)
    return dest


def convert(path, out, val_out, min_elo, max_games, min_ply, max_ply, min_base_time, val_frac, seed):
    rng = random.Random(seed)
    out = Path(out)
    val_out = Path(val_out) if val_out else None
    out.parent.mkdir(parents=True, exist_ok=True)
    if val_out:
        val_out.parent.mkdir(parents=True, exist_ok=True)

    n_train = n_val = 0
    with open(out, 'w', encoding='utf-8') as train_f:
        val_f = open(val_out, 'w', encoding='utf-8') if val_out else None
        try:
            for record in iter_pgn_records(
                path,
                max_games=max_games,
                min_elo=min_elo,
                min_ply=min_ply,
                max_ply=max_ply,
                min_base_time=min_base_time,
            ):
                line = json.dumps(record) + '\n'
                if val_f is not None and rng.random() < val_frac:
                    val_f.write(line)
                    n_val += 1
                else:
                    train_f.write(line)
                    n_train += 1
                total = n_train + n_val
                if total % 20000 == 0:
                    print(f'{total} posições…')
        finally:
            if val_f:
                val_f.close()

    print(f'treino: {n_train} posições -> {out}')
    if val_out:
        print(f'validação: {n_val} posições -> {val_out}')


def main():
    parser = argparse.ArgumentParser(
        description='Prepara dump Lichess (PGN ou .pgn.zst) filtrado por Elo.'
    )
    parser.add_argument('--input', help='PGN ou .pgn.zst já baixado')
    parser.add_argument('--download', metavar='YYYY-MM', help='baixa o dump mensal do Lichess')
    parser.add_argument('--min-elo', type=int, default=2200)
    parser.add_argument('--max-games', type=int, default=None)
    parser.add_argument('--min-ply', type=int, default=8)
    parser.add_argument('--max-ply', type=int, default=80)
    parser.add_argument('--min-base-time', type=int, default=180, help='ignora bullet (segundos de base)')
    parser.add_argument('--val-frac', type=float, default=0.05)
    parser.add_argument('--out', default='data/lichess_high_elo.jsonl')
    parser.add_argument('--val-out', default='data/lichess_high_elo_val.jsonl')
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()

    source = args.input
    if args.download:
        source = str(download(args.download, f'data/lichess_db_standard_rated_{args.download}.pgn.zst'))
    if not source:
        parser.error('passe --input arquivo.pgn.zst ou --download YYYY-MM')

    convert(
        source,
        args.out,
        args.val_out,
        min_elo=args.min_elo,
        max_games=args.max_games,
        min_ply=args.min_ply,
        max_ply=args.max_ply,
        min_base_time=args.min_base_time,
        val_frac=args.val_frac,
        seed=args.seed,
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
