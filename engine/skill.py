import random
from dataclasses import dataclass
from typing import Optional


SKILL_ORDER = ('iniciante', 'facil', 'medio', 'dificil', 'mestre')

SKILL_LABELS = {
    'iniciante': 'Iniciante',
    'facil': 'Fácil',
    'medio': 'Médio',
    'dificil': 'Difícil',
    'mestre': 'Mestre',
}


@dataclass(frozen=True)
class Skill:
    name: str
    depth: int
    nodes: Optional[int] = None
    time_ms: Optional[int] = None
    noise_std: float = 0.0
    alt_move_p: float = 0.0
    use_network: bool = False  # policy só na raiz; eval da árvore é clássica


SKILLS = {
    'iniciante': Skill('iniciante', depth=2, nodes=500, noise_std=90, alt_move_p=0.4),
    'facil': Skill('facil', depth=3, nodes=2500, noise_std=45, alt_move_p=0.2),
    'medio': Skill('medio', depth=4, nodes=10000, noise_std=15, alt_move_p=0.1),
    'dificil': Skill('dificil', depth=7, nodes=80000, noise_std=5, alt_move_p=0.05, use_network=True),
    'mestre': Skill('mestre', depth=16, time_ms=4000, noise_std=0, alt_move_p=0, use_network=True),
}

# Destilada: policy SF na raiz, eval clássica na árvore (mais profundidade).
SF_SKILLS = {
    'iniciante': Skill('iniciante', depth=3, nodes=1500, noise_std=70, alt_move_p=0.35, use_network=True),
    'facil': Skill('facil', depth=4, nodes=5000, noise_std=35, alt_move_p=0.18, use_network=True),
    'medio': Skill('medio', depth=6, nodes=18000, noise_std=10, alt_move_p=0.06, use_network=True),
    'dificil': Skill('dificil', depth=10, time_ms=2500, noise_std=0, alt_move_p=0, use_network=True),
    'mestre': Skill('mestre', depth=20, time_ms=3500, noise_std=0, alt_move_p=0, use_network=True),
}


def get_skill(name_or_index, kind='own'):
    if isinstance(name_or_index, int):
        name_or_index = SKILL_ORDER[name_or_index]
    table = SF_SKILLS if kind == 'sf' else SKILLS
    if name_or_index not in table:
        raise KeyError(f'nível desconhecido: {name_or_index}')
    return table[name_or_index]


def pick_from_scores(scored_moves, alt_move_p, rng=None):
    """scored_moves: lista (score, move) ordenada da melhor para a pior."""
    rng = rng or random
    if not scored_moves:
        return None
    best_score, best_move = scored_moves[0]
    if len(scored_moves) == 1 or alt_move_p <= 0 or rng.random() >= alt_move_p:
        return best_move
    top = scored_moves[: min(3, len(scored_moves))]
    weights = []
    for score, _move in top:
        weights.append(2 ** ((score - best_score) / 100.0))
    total = sum(weights) or 1.0
    pick = rng.random() * total
    acc = 0.0
    for weight, (_, move) in zip(weights, top):
        acc += weight
        if pick <= acc:
            return move
    return top[-1][1]
