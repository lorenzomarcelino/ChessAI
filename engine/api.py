from engine.board import EngineBoard
from engine.search import Searcher
from engine.skill import get_skill, pick_from_scores


def think(
    fen=None,
    depth=None,
    nodes=None,
    time_ms=None,
    remaining_ms=None,
    skill=None,
    use_network=None,
    engine_kind='own',
):
    """Devolve o melhor lance em UCI. Sem limites, usa profundidade 4.

    engine_kind: 'own' (CNN própria, eval clássica) ou 'sf' (policy destilada na raiz).
    """
    from engine import nn_eval

    board = EngineBoard.from_fen(fen) if fen else EngineBoard()
    if board.is_game_over:
        return None

    kind = nn_eval.set_kind(engine_kind)
    noise_std = 0
    collect_root = False
    alt_move_p = 0
    network = False if use_network is None else use_network
    use_leaf_eval = False

    if skill is not None:
        spec = get_skill(skill, kind=kind)
        depth = spec.depth if depth is None else depth
        nodes = spec.nodes if nodes is None else nodes
        time_ms = spec.time_ms if time_ms is None else time_ms
        noise_std = spec.noise_std
        alt_move_p = spec.alt_move_p
        collect_root = alt_move_p > 0
        if use_network is None:
            network = spec.use_network and nn_eval.network_available()

    if noise_std < 20:
        from engine.book import probe
        booked = probe(board)
        if booked:
            return booked

    max_depth = depth if depth is not None else (64 if time_ms or remaining_ms or nodes else 4)
    searcher = Searcher()
    move = searcher.search(
        board,
        depth=max_depth,
        nodes=nodes,
        time_ms=time_ms,
        remaining_ms=remaining_ms,
        noise_std=noise_std,
        use_network=network,
        use_leaf_eval=use_leaf_eval,
        collect_root=collect_root,
    )
    if collect_root and searcher.root_scores:
        searcher.root_scores.sort(key=lambda item: item[0], reverse=True)
        picked = pick_from_scores(searcher.root_scores, alt_move_p)
        if picked is not None:
            return picked.uci()
    return move
