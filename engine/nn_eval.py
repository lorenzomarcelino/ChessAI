"""Inferência da rede com fallback. Importa torch só quando há checkpoint.

Dois perfis:
- own: CNN `value_v1.pt` (tentativa 100% própria) — policy só na raiz
- sf: MLP `value_sf.pt` (rótulos Stockfish) — eval nas folhas + policy na raiz
"""

from pathlib import Path

import numpy as np

MODELS_DIR = Path(__file__).resolve().parents[1] / 'models'
VALUE_SCALE = 400.0
KIND_OWN = 'own'
KIND_SF = 'sf'
OWN_CHECKPOINTS = ('value_v2.pt', 'value_v1.pt')
SF_CHECKPOINT = 'value_sf.pt'

_kind = KIND_OWN
_net = None
_device = None
_loaded_path = None
_eval_cache = {}


def set_kind(kind):
    global _kind
    kind = KIND_SF if kind == KIND_SF else KIND_OWN
    if kind != _kind:
        reset_cache()
        _kind = kind
    return _kind


def current_kind():
    return _kind


def best_checkpoint(kind=None):
    kind = _kind if kind is None else kind
    if kind == KIND_SF:
        path = MODELS_DIR / SF_CHECKPOINT
        return path if path.is_file() else None
    for name in OWN_CHECKPOINTS:
        path = MODELS_DIR / name
        if path.is_file():
            return path
    return None


def network_available(kind=None):
    return best_checkpoint(kind) is not None


def _ensure_net():
    global _net, _device, _loaded_path
    path = best_checkpoint()
    if path is None:
        return None
    if _net is not None and _loaded_path == path:
        return _net
    import torch
    from engine.network import load_net

    _device = torch.device('cpu')
    try:
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    _net, _ = load_net(path, device=_device)
    _loaded_path = path
    return _net


def _encode_tensor(board):
    import torch
    from engine.encode import encode_board

    planes = encode_board(board)
    return torch.from_numpy(planes).unsqueeze(0)


def infer(board):
    """Devolve (policy_logits np[4096], value_cp int) ou None se não houver modelo."""
    net = _ensure_net()
    if net is None:
        return None
    import torch

    tensor = _encode_tensor(board)
    with torch.no_grad():
        policy, value = net(tensor)
    value_cp = int(value.item() * VALUE_SCALE)
    return policy.squeeze(0).cpu().numpy(), value_cp


def value_cp(board):
    net = _ensure_net()
    if net is None:
        return None
    import chess.polyglot
    import torch

    raw = board.raw if hasattr(board, 'raw') else board
    key = chess.polyglot.zobrist_hash(raw)
    cached = _eval_cache.get(key)
    if cached is not None:
        return cached

    tensor = _encode_tensor(raw)
    with torch.no_grad():
        if hasattr(net, 'forward_value'):
            value = net.forward_value(tensor)
        else:
            _policy, value = net(tensor)
    score = int(value.item() * VALUE_SCALE)
    if len(_eval_cache) > 200_000:
        _eval_cache.clear()
    _eval_cache[key] = score
    return score


def policy_score(board, move):
    result = infer(board)
    if result is None:
        return 0
    from engine.encode import policy_index_for_board
    logits, _ = result
    idx = policy_index_for_board(board, move)
    return float(logits[idx])


def clear_eval_cache():
    _eval_cache.clear()


def reset_cache():
    global _net, _device, _loaded_path
    _net = None
    _device = None
    _loaded_path = None
    clear_eval_cache()
