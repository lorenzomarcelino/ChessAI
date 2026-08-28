"""Treino supervisionado da CNN (Fase 3.1)."""

import argparse
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, random_split

from engine.encode import INPUT_PLANES
from engine.network import ValuePolicyNet, save_checkpoint, load_net
from train.dataset import JsonlIterableDataset, PositionDataset, load_jsonl, load_pgn, sample_jsonl


def collate(batch):
    planes = torch.from_numpy(np.stack([item[0] for item in batch]))
    policy = torch.tensor([item[1] for item in batch], dtype=torch.long)
    value = torch.tensor([item[2] for item in batch], dtype=torch.float32)
    return planes, policy, value


def train_one_epoch(model, loader, optimizer, device, log_every=50_000):
    model.train()
    total = 0.0
    n = 0
    last_log = 0
    for planes, policy, value in loader:
        planes = planes.to(device)
        policy = policy.to(device)
        value = value.to(device)
        optimizer.zero_grad()
        logits, pred_value = model(planes)
        loss = nn.functional.cross_entropy(logits, policy) + nn.functional.mse_loss(pred_value, value)
        loss.backward()
        optimizer.step()
        total += loss.item() * planes.size(0)
        n += planes.size(0)
        if log_every and n - last_log >= log_every:
            print(f'  {n} amostras  loss={total / n:.4f}', flush=True)
            last_log = n
    return total / max(n, 1)


@torch.no_grad()
def validate(model, loader, device):
    model.eval()
    total = 0.0
    n = 0
    for planes, policy, value in loader:
        planes = planes.to(device)
        policy = policy.to(device)
        value = value.to(device)
        logits, pred_value = model(planes)
        loss = nn.functional.cross_entropy(logits, policy) + nn.functional.mse_loss(pred_value, value)
        total += loss.item() * planes.size(0)
        n += planes.size(0)
    return total / max(n, 1)


def make_loaders(args):
    path = Path(args.data)
    suffix = path.suffix.lower()
    if suffix == '.zst' or str(path).endswith('.pgn.zst') or (
        suffix == '.pgn' and path.stat().st_size > 80_000_000 and not args.max_games
    ):
        raise SystemExit(
            'PGN grande demais para carregar na RAM. '
            'Primeiro: python -m train.prepare_lichess --input arquivo.pgn.zst --min-elo 2200'
        )

    if suffix == '.pgn':
        records = load_pgn(path, max_games=args.max_games, min_elo=args.min_elo)
        dataset = PositionDataset(records)
        val_size = max(1, len(dataset) // 10)
        train_size = len(dataset) - val_size
        train_set, val_set = random_split(dataset, [train_size, val_size])
        train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True, collate_fn=collate)
        val_loader = DataLoader(val_set, batch_size=args.batch_size, collate_fn=collate)
        return train_loader, val_loader, len(records)

    if getattr(args, 'max_samples', None):
        print(f'amostrando até {args.max_samples} posições de {path}…', flush=True)
        train_records, seen = sample_jsonl(path, args.max_samples, seed=args.seed)
        print(f'treino: {len(train_records)} / {seen} posições', flush=True)
        train_loader = DataLoader(
            PositionDataset(train_records),
            batch_size=args.batch_size,
            shuffle=True,
            collate_fn=collate,
        )
        if args.val:
            val_k = max(8, min(args.max_samples // 10, 20_000))
            print(f'amostrando até {val_k} posições de {args.val}…', flush=True)
            val_records, val_seen = sample_jsonl(args.val, val_k, seed=args.seed + 1)
            print(f'validação: {len(val_records)} / {val_seen} posições', flush=True)
            val_loader = DataLoader(
                PositionDataset(val_records),
                batch_size=args.batch_size,
                collate_fn=collate,
            )
        else:
            dataset = PositionDataset(train_records)
            val_size = max(1, len(dataset) // 10)
            train_size = len(dataset) - val_size
            train_set, val_set = random_split(dataset, [train_size, val_size])
            train_loader = DataLoader(
                train_set, batch_size=args.batch_size, shuffle=True, collate_fn=collate
            )
            val_loader = DataLoader(val_set, batch_size=args.batch_size, collate_fn=collate)
        return train_loader, val_loader, len(train_records)

    if args.val:
        train_loader = DataLoader(
            JsonlIterableDataset(path),
            batch_size=args.batch_size,
            collate_fn=collate,
        )
        val_loader = DataLoader(
            JsonlIterableDataset(args.val),
            batch_size=args.batch_size,
            collate_fn=collate,
        )
        return train_loader, val_loader, None

    records = load_jsonl(path)
    dataset = PositionDataset(records)
    val_size = max(1, len(dataset) // 10)
    train_size = len(dataset) - val_size
    train_set, val_set = random_split(dataset, [train_size, val_size])
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True, collate_fn=collate)
    val_loader = DataLoader(val_set, batch_size=args.batch_size, collate_fn=collate)
    return train_loader, val_loader, len(records)


def main():
    parser = argparse.ArgumentParser(description='Treina ValuePolicyNet.')
    parser.add_argument('--data', required=True, help='JSONL (recomendado) ou PGN pequeno')
    parser.add_argument('--val', default=None, help='JSONL de validação (dumps grandes)')
    parser.add_argument('--epochs', type=int, default=2)
    parser.add_argument('--batch-size', type=int, default=128)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--out', default='models/value_v1.pt')
    parser.add_argument('--resume', default=None, help='checkpoint para continuar o treino')
    parser.add_argument('--max-samples', type=int, default=300_000, help='0 = JSONL inteiro (lento no CPU)')
    parser.add_argument('--max-games', type=int, default=None)
    parser.add_argument('--min-elo', type=int, default=0)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()
    if args.max_samples == 0:
        args.max_samples = None

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    train_loader, val_loader, n_records = make_loaders(args)
    if n_records is not None and n_records < 8:
        raise SystemExit(f'dataset pequeno demais: {n_records} posições')

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'device={device}')
    if args.resume:
        model, _ = load_net(args.resume, device=device)
        model.train()
    else:
        model = ValuePolicyNet(in_planes=INPUT_PLANES).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    best = None
    for epoch in range(1, args.epochs + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, device)
        val_loss = validate(model, val_loader, device)
        print(f'epoch {epoch} train={train_loss:.4f} val={val_loss:.4f}')
        if best is None or val_loss < best:
            best = val_loss
            save_checkpoint(
                model,
                args.out,
                extra={'trained': True, 'epoch': epoch, 'val_loss': val_loss, 'seed': args.seed},
            )
    print(f'melhor checkpoint em {args.out} (val={best:.4f})')


if __name__ == '__main__':
    main()
