import chess
import chess.polyglot

from engine.evaluate import PIECE_VALUES, evaluate
from engine.time_manager import TimeManager


INF = 50_000
MATE = 32_000
MATE_BOUND = 30_000
MAX_PLY = 64
EXACT, LOWER, UPPER = 0, 1, 2


class SearchTimeout(Exception):
    pass


class Searcher:
    def __init__(self):
        self.tt = {}
        self.killers = [[None, None] for _ in range(MAX_PLY)]
        self.history = [[[0] * 64 for _ in range(64)] for _ in range(2)]
        self.nodes = 0
        self.time_manager = TimeManager()
        self.root_move = None
        self.completed_depth = 0
        self.root_scores = []
        self.noise_std = 0
        self.use_network = False
        self.use_leaf_eval = False
        self.root_policy = None

    def search(
        self,
        board,
        depth=4,
        nodes=None,
        time_ms=None,
        remaining_ms=None,
        noise_std=0,
        use_network=False,
        use_leaf_eval=False,
        collect_root=False,
    ):
        raw = board.raw
        self.tt.clear()
        self.killers = [[None, None] for _ in range(MAX_PLY)]
        self.history = [[[0] * 64 for _ in range(64)] for _ in range(2)]
        self.nodes = 0
        self.completed_depth = 0
        self.root_scores = []
        self.noise_std = noise_std
        self.use_network = False
        self.use_leaf_eval = use_leaf_eval
        self.root_policy = None
        self.collect_root = collect_root

        moves = list(raw.legal_moves)
        if not moves:
            return None

        # Carrega a rede antes do relógio — senão o 1º lance come o tempo todo.
        if use_network or use_leaf_eval:
            from engine import nn_eval
            nn_eval.clear_eval_cache()
            inferred = nn_eval.infer(raw)
            if inferred is not None:
                self.root_policy = inferred[0]

        self.time_manager = TimeManager(time_ms=time_ms, remaining_ms=remaining_ms, max_nodes=nodes)
        self.time_manager.start()

        best_move = moves[0]
        max_depth = depth if depth is not None else 64

        for current_depth in range(1, max_depth + 1):
            try:
                self.root_move = None
                self._negamax(raw, current_depth, -INF, INF, 0)
                if self.root_move is not None:
                    best_move = self.root_move
                self.completed_depth = current_depth
            except SearchTimeout:
                break

            if nodes is not None and self.nodes >= nodes:
                break
            if self.time_manager.deadline is not None:
                if self.time_manager.on_node():
                    break

        return best_move.uci()

    def _probe_tt(self, key, depth, alpha, beta, ply):
        entry = self.tt.get(key)
        if entry is None:
            return None, None
        stored_depth, score, flag, move = entry
        score = self._from_tt_score(score, ply)
        if stored_depth < depth:
            return None, move
        if flag == EXACT:
            return score, move
        if flag == LOWER and score >= beta:
            return score, move
        if flag == UPPER and score <= alpha:
            return score, move
        return None, move

    def _store_tt(self, key, depth, score, flag, move, ply):
        if score > MATE_BOUND:
            score += ply
        elif score < -MATE_BOUND:
            score -= ply
        self.tt[key] = (depth, score, flag, move)

    def _from_tt_score(self, score, ply):
        if score is None:
            return None
        if score > MATE_BOUND:
            return score - ply
        if score < -MATE_BOUND:
            return score + ply
        return score

    def _ordered_moves(self, board, tt_move, ply, captures_only=False):
        moves = list(board.generate_legal_captures() if captures_only else board.legal_moves)
        scored = []
        killers = self.killers[ply] if ply < MAX_PLY else (None, None)
        color = 0 if board.turn == chess.WHITE else 1
        for move in moves:
            if move == tt_move:
                score = 1_000_000
            elif board.is_capture(move):
                score = 100_000 + _mvv_lva(board, move)
            elif move == killers[0]:
                score = 90_000
            elif move == killers[1]:
                score = 80_000
            else:
                score = self.history[color][move.from_square][move.to_square]
                if ply == 0 and self.root_policy is not None and not captures_only:
                    from engine.encode import policy_index_for_board
                    score += int(self.root_policy[policy_index_for_board(board, move)])
            scored.append((score, move))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [move for _, move in scored]

    def _update_quiet(self, move, ply, depth, color_index):
        if ply < MAX_PLY:
            if self.killers[ply][0] != move:
                self.killers[ply][1] = self.killers[ply][0]
                self.killers[ply][0] = move
        self.history[color_index][move.from_square][move.to_square] += depth * depth

    def _negamax(self, board, depth, alpha, beta, ply):
        if self.time_manager.on_node():
            raise SearchTimeout()
        self.nodes += 1

        if ply > 0 and (board.is_repetition() or board.is_fifty_moves()):
            return 0

        key = chess.polyglot.zobrist_hash(board)
        original_alpha = alpha
        tt_score, tt_move = self._probe_tt(key, depth, alpha, beta, ply)
        if tt_score is not None and ply > 0:
            return tt_score

        if depth <= 0 or ply >= MAX_PLY - 1:
            return self._quiescence(board, alpha, beta, ply)

        in_check = board.is_check()
        if (
            depth >= 3
            and ply > 0
            and not in_check
            and beta < MATE_BOUND
            and _has_non_pawn_material(board)
        ):
            board.push(chess.Move.null())
            try:
                score = -self._negamax(board, depth - 3, -beta, -beta + 1, ply + 1)
            finally:
                board.pop()
            if score >= beta:
                return score

        moves = self._ordered_moves(board, tt_move, ply)
        if not moves:
            return -MATE + ply if in_check else 0

        best_move = moves[0]
        best_score = -INF
        color_index = 0 if board.turn == chess.WHITE else 1
        if ply == 0:
            self.root_scores = []

        for move in moves:
            board.push(move)
            try:
                child_depth = depth - 1
                if board.is_check() and ply < 18:
                    child_depth = depth
                score = -self._negamax(board, child_depth, -beta, -alpha, ply + 1)
            finally:
                board.pop()

            if ply == 0 and self.collect_root:
                self.root_scores.append((score, move))

            if score > best_score:
                best_score = score
                best_move = move
                if ply == 0:
                    self.root_move = move

            if score > alpha:
                alpha = score
            if alpha >= beta and not (ply == 0 and self.collect_root):
                if not board.is_capture(move):
                    self._update_quiet(move, ply, depth, color_index)
                break

        flag = EXACT
        if best_score <= original_alpha:
            flag = UPPER
        elif best_score >= beta:
            flag = LOWER
        self._store_tt(key, depth, best_score, flag, best_move, ply)
        return best_score

    def _quiescence(self, board, alpha, beta, ply):
        if self.time_manager.on_node():
            raise SearchTimeout()
        self.nodes += 1

        if board.is_check():
            moves = self._ordered_moves(board, None, ply, captures_only=False)
            if not moves:
                return -MATE + ply
            stand_pat = None
        else:
            stand_pat = evaluate(board, noise_std=self.noise_std, use_network=self.use_leaf_eval)
            if stand_pat >= beta:
                return stand_pat
            if stand_pat > alpha:
                alpha = stand_pat
            moves = self._ordered_moves(board, None, ply, captures_only=True)

        best = stand_pat if stand_pat is not None else -INF
        for move in moves:
            if stand_pat is not None and board.is_capture(move):
                if stand_pat + _capture_value(board, move) + 200 < alpha:
                    continue
            board.push(move)
            try:
                score = -self._quiescence(board, -beta, -alpha, ply + 1)
            finally:
                board.pop()
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                return alpha
        return best


def _has_non_pawn_material(board):
    us = board.occupied_co[board.turn]
    return bool(us & ~board.pawns & ~board.kings)


def _mvv_lva(board, move):
    if board.is_en_passant(move):
        victim = chess.PAWN
    else:
        captured = board.piece_at(move.to_square)
        victim = captured.piece_type if captured else chess.PAWN
    attacker = board.piece_at(move.from_square).piece_type
    return PIECE_VALUES[victim] * 16 - PIECE_VALUES[attacker]


def _capture_value(board, move):
    if board.is_en_passant(move):
        return PIECE_VALUES[chess.PAWN]
    captured = board.piece_at(move.to_square)
    if captured is None:
        return 0
    return PIECE_VALUES[captured.piece_type]
