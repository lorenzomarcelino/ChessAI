"""Rotula posições com eval e melhor lance do Stockfish. O SF não joga no app."""

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

import chess
import chess.engine

from train.stockfish_bin import ensure_stockfish

VALUE_SCALE = 400.0


def stm_value_from_score(score):
    """Score python-chess → tanh no ponto de vista de quem joga."""
    cp = score.relative.score(mate_score=10_000)
    if cp is None:
        return None
    cp = max(-10_000, min(10_000, int(cp)))
    return math.tanh(cp / VALUE_SCALE)


def iter_source_fens(path, seed=0):
    rng = random.Random(seed)
    with open(path, encoding='utf-8') as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            # mistura o arquivo sem carregar tudo: fica 1 em 20 em média
            if rng.random() > 0.08:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            fen = record.get('fen')
            if fen:
                yield fen, record.get('move')


def annotate_position(engine, fen, depth):
    board = chess.Board(fen)
    if board.is_game_over():
        return None
    info = engine.analyse(board, chess.engine.Limit(depth=depth))
    value = stm_value_from_score(info['score'])
    if value is None:
        return None
    pv = info.get('pv') or []
    if not pv:
        return None
    move = pv[0]
    if move not in board.legal_moves:
        return None
    return {'fen': fen, 'move': move.uci(), 'value': round(value, 6)}


def distill(
    source,
    out,
    depth=12,
    hours=9.0,
    threads=None,
    hash_mb=256,
    stockfish=None,
    seed=0,
    log_every=25,
):
    source = Path(source)
    out = Path(out)
    if not source.is_file():
        raise SystemExit(f'arquivo de origem não encontrado: {source}')

    binary = ensure_stockfish(stockfish)
    out.parent.mkdir(parents=True, exist_ok=True)

    import os
    if threads is None:
        threads = max(1, (os.cpu_count() or 4) - 1)

    deadline = time.time() + max(60.0, hours * 3600.0)
    started = time.time()
    written = 0
    skipped = 0

    popen_args = {}
    if sys.platform == 'win32':
        import subprocess
        popen_args['creationflags'] = subprocess.CREATE_NO_WINDOW

    print(
        f'Stockfish={binary}  depth={depth}  threads={threads}  '
        f'orçamento={hours:.1f}h  saída={out}',
        flush=True,
    )

    engine = chess.engine.SimpleEngine.popen_uci(str(binary), **popen_args)
    try:
        engine.configure({'Threads': threads, 'Hash': hash_mb})
        with open(out, 'a', encoding='utf-8') as handle:
            for fen, _orig_move in iter_source_fens(source, seed=seed):
                if time.time() >= deadline:
                    print('tempo de rotulagem esgotado.', flush=True)
                    break
                try:
                    labeled = annotate_position(engine, fen, depth)
                except (chess.engine.EngineError, chess.engine.EngineTerminatedError) as exc:
                    print(f'engine error: {exc}', flush=True)
                    skipped += 1
                    continue
                if labeled is None:
                    skipped += 1
                    continue
                handle.write(json.dumps(labeled) + '\n')
                written += 1
                if written % 10 == 0:
                    handle.flush()
                if written % log_every == 0:
                    elapsed = time.time() - started
                    rate = written / max(elapsed, 1e-6)
                    remain = max(0.0, deadline - time.time())
                    print(
                        f'{written} rótulos  {rate:.2f}/s  '
                        f'resta {remain / 3600:.2f}h  skip={skipped}',
                        flush=True,
                    )
    except KeyboardInterrupt:
        print(
            f'interrompeu com {written} rótulos em {out}. '
            'depois: python -m train.sf_teacher --train-only',
            flush=True,
        )
        raise
    finally:
        engine.quit()

    elapsed = time.time() - started
    print(f'rotulagem: {written} posições em {elapsed / 60:.1f} min -> {out}', flush=True)
    return written


def main():
    parser = argparse.ArgumentParser(description='Destila rótulos com Stockfish.')
    parser.add_argument('--data', default='data/lichess_high_elo.jsonl')
    parser.add_argument('--out', default='data/sf_labels.jsonl')
    parser.add_argument('--depth', type=int, default=12)
    parser.add_argument('--hours', type=float, default=9.0)
    parser.add_argument('--threads', type=int, default=None)
    parser.add_argument('--hash-mb', type=int, default=256)
    parser.add_argument('--stockfish', default=None)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()
    distill(
        args.data,
        args.out,
        depth=args.depth,
        hours=args.hours,
        threads=args.threads,
        hash_mb=args.hash_mb,
        stockfish=args.stockfish,
        seed=args.seed,
    )


if __name__ == '__main__':
    main()
