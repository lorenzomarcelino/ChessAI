import math

import torch
from chess.engine import Cp, Mate, PovScore
import chess

from engine.api import think
from engine.board import EngineBoard
from engine.encode import INPUT_PLANES, POLICY_SIZE, encode_fen
from engine.network import CompactNet, count_parameters, load_net, save_checkpoint
from engine.nn_eval import KIND_OWN, KIND_SF, reset_cache, set_kind
from engine.skill import get_skill
from train.distill_stockfish import stm_value_from_score


def test_compact_forward_shapes():
    model = CompactNet()
    model.eval()
    batch = torch.from_numpy(encode_fen(
        'rnbqkbnr/pppppppp/8/8/8/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1'
    )).unsqueeze(0)
    policy, value = model(batch)
    assert policy.shape == (1, POLICY_SIZE)
    assert value.shape == (1,)
    with torch.no_grad():
        only_value = model.forward_value(batch)
    assert torch.allclose(value, only_value)


def test_compact_is_smaller_than_two_million():
    n = count_parameters(CompactNet())
    assert 200_000 <= n <= 2_000_000


def test_compact_save_load(tmp_path):
    path = tmp_path / 'sf.pt'
    model = CompactNet(hidden=64, mid=16)
    save_checkpoint(model, path, extra={'teacher': 'stockfish'})
    loaded, payload = load_net(path)
    assert payload['arch'] == CompactNet.ARCH
    assert payload['teacher'] == 'stockfish'
    x = torch.zeros(2, INPUT_PLANES, 8, 8)
    with torch.no_grad():
        p1, v1 = model(x)
        p2, v2 = loaded(x)
    assert torch.allclose(p1, p2)
    assert torch.allclose(v1, v2)


def test_stm_value_from_cp():
    score = PovScore(Cp(400), chess.WHITE)
    assert abs(stm_value_from_score(score) - math.tanh(1.0)) < 1e-6


def test_stm_value_from_mate():
    score = PovScore(Mate(1), chess.WHITE)
    assert stm_value_from_score(score) > 0.99


def test_sf_skill_has_master_time():
    assert get_skill('mestre', kind='sf').time_ms >= 2500
    assert get_skill('mestre', kind='sf').depth >= get_skill('mestre').depth


def test_think_sf_without_checkpoint_still_moves():
    reset_cache()
    set_kind(KIND_SF)
    try:
        board = EngineBoard()
        move = think(skill='iniciante', engine_kind='sf')
        assert move in board.legal_moves()
    finally:
        reset_cache()
        set_kind(KIND_OWN)
