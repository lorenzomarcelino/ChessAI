from pathlib import Path

import torch

from engine.encode import INPUT_PLANES, POLICY_SIZE, encode_fen
from engine.network import ValuePolicyNet, count_parameters, save_checkpoint, load_net, export_untrained


def test_forward_shapes_and_no_nan():
    model = ValuePolicyNet()
    model.eval()
    batch = torch.from_numpy(encode_fen(
        'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    )).unsqueeze(0).repeat(8, 1, 1, 1)
    assert batch.shape == (8, INPUT_PLANES, 8, 8)
    policy, value = model(batch)
    assert policy.shape == (8, POLICY_SIZE)
    assert value.shape == (8,)
    assert torch.isfinite(policy).all()
    assert torch.isfinite(value).all()
    assert (value >= -1).all() and (value <= 1).all()


def test_parameter_count_is_small():
    n = count_parameters(ValuePolicyNet())
    assert 100_000 <= n <= 2_000_000


def test_save_and_load(tmp_path):
    path = tmp_path / 'net.pt'
    model = ValuePolicyNet()
    save_checkpoint(model, path, extra={'trained': False})
    loaded, payload = load_net(path)
    assert payload['params'] == count_parameters(model)
    x = torch.zeros(1, INPUT_PLANES, 8, 8)
    with torch.no_grad():
        p1, v1 = model(x)
        p2, v2 = loaded(x)
    assert torch.allclose(p1, p2)
    assert torch.allclose(v1, v2)


def test_export_untrained(tmp_path, monkeypatch):
    dest = tmp_path / 'untrained.pt'
    path, n = export_untrained(dest)
    assert Path(path).is_file()
    assert n > 0
