import torch
from torch.utils.data import DataLoader

from engine.network import ValuePolicyNet
from train.dataset import PositionDataset
from train.train import collate, train_one_epoch


def test_sample_jsonl_keeps_k_records(tmp_path):
    from train.dataset import sample_jsonl

    path = tmp_path / 'tiny.jsonl'
    lines = ['{"fen": "x", "move": "e2e4", "value": 0.0}\n' for _ in range(40)]
    path.write_text(''.join(lines), encoding='utf-8')
    records, seen = sample_jsonl(path, 10, seed=0)
    assert seen == 40
    assert len(records) == 10
    assert records[0]['move'] == 'e2e4'


def test_one_training_step_finite_loss():
    records = [
        {
            'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
            'move': 'e2e4',
            'value': 0.0,
        }
        for _ in range(8)
    ]
    loader = DataLoader(PositionDataset(records), batch_size=4, collate_fn=collate)
    model = ValuePolicyNet()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss = train_one_epoch(model, loader, optimizer, torch.device('cpu'))
    assert loss == loss  # not NaN
