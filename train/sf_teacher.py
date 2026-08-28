"""Pipeline overnight: Stockfish rotula → treina CompactNet → models/value_sf.pt.

O Stockfish não entra no jogo. Só gera alvos. No menu: Oponente → Destilada.
"""

import argparse
import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, random_split

from engine.encode import INPUT_PLANES
from engine.network import CompactNet, save_checkpoint
from train.dataset import PositionDataset, load_jsonl
from train.distill_stockfish import distill
from train.train import collate, train_one_epoch, validate


def train_compact(data, out, epochs=8, batch_size=256, lr=1e-3, seed=0, val_frac=0.05):
    records = load_jsonl(data)
    if len(records) < 64:
        raise SystemExit(
            f'dataset destilado pequeno demais ({len(records)}). '
            'rode a rotulagem por mais tempo.'
        )
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    dataset = PositionDataset(records)
    val_size = max(32, int(len(dataset) * val_frac))
    train_size = len(dataset) - val_size
    train_set, val_set = random_split(dataset, [train_size, val_size])
    train_loader = DataLoader(
        train_set, batch_size=batch_size, shuffle=True, collate_fn=collate
    )
    val_loader = DataLoader(val_set, batch_size=batch_size, collate_fn=collate)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'treino compacto  device={device}  n={len(records)}', flush=True)
    model = CompactNet().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    best = None
    for epoch in range(1, epochs + 1):
        train_loss = train_one_epoch(
            model, train_loader, optimizer, device, log_every=20_000
        )
        val_loss = validate(model, val_loader, device)
        print(f'epoch {epoch}/{epochs} train={train_loss:.4f} val={val_loss:.4f}', flush=True)
        if best is None or val_loss < best:
            best = val_loss
            save_checkpoint(
                model,
                out,
                extra={
                    'trained': True,
                    'teacher': 'stockfish',
                    'epoch': epoch,
                    'val_loss': val_loss,
                    'n': len(records),
                    'in_planes': INPUT_PLANES,
                },
            )
    print(f'melhor checkpoint em {out} (val={best:.4f})', flush=True)
    return out


def main():
    parser = argparse.ArgumentParser(
        description='Rotula com Stockfish e treina a engine destilada.'
    )
    parser.add_argument('--data', default='data/lichess_high_elo.jsonl')
    parser.add_argument('--labels', default='data/sf_labels.jsonl')
    parser.add_argument('--out', default='models/value_sf.pt')
    parser.add_argument('--hours', type=float, default=10.0, help='orçamento total')
    parser.add_argument('--depth', type=int, default=12)
    parser.add_argument('--threads', type=int, default=None)
    parser.add_argument('--epochs', type=int, default=8)
    parser.add_argument('--batch-size', type=int, default=256)
    parser.add_argument('--stockfish', default=None)
    parser.add_argument('--train-only', action='store_true')
    parser.add_argument('--distill-only', action='store_true')
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()

    labels = Path(args.labels)
    if not args.train_only:
        source = Path(args.data)
        if not source.is_file():
            raise SystemExit(
                f'precisa de {source}. gere com prepare_lichess '
                '(o JSONL de Elo alto que você já tem).'
            )
        label_hours = args.hours if args.distill_only else max(0.5, args.hours * 0.88)
        print(
            '=== 1/2 rotulagem Stockfish ===\n'
            'O SF só gera alvos. Não joga no Pygame.',
            flush=True,
        )
        n = distill(
            source,
            labels,
            depth=args.depth,
            hours=label_hours,
            threads=args.threads,
            stockfish=args.stockfish,
            seed=args.seed,
        )
        if n == 0 and not labels.is_file():
            raise SystemExit('nenhum rótulo gerado.')

    if args.distill_only:
        return

    print('=== 2/2 treino CompactNet ===', flush=True)
    train_compact(
        labels,
        args.out,
        epochs=args.epochs,
        batch_size=args.batch_size,
        seed=args.seed,
    )
    print(
        'pronto. no jogo: Oponente → Destilada  (Difícil / Mestre).\n'
        'Oponente → Própria continua a CNN 100% nossa.',
        flush=True,
    )


if __name__ == '__main__':
    main()
