import chess


class EngineBoard:
    """Tabuleiro legal rápido, sem Pygame. Make/unmake via push/pop."""

    def __init__(self, fen=None):
        self._board = chess.Board(fen) if fen else chess.Board()

    @classmethod
    def from_fen(cls, fen):
        return cls(fen)

    def to_fen(self):
        return self._board.fen()

    @property
    def raw(self):
        return self._board

    @property
    def turn(self):
        return 'white' if self._board.turn == chess.WHITE else 'black'

    @property
    def is_check(self):
        return self._board.is_check()

    @property
    def is_checkmate(self):
        return self._board.is_checkmate()

    @property
    def is_stalemate(self):
        return self._board.is_stalemate()

    @property
    def is_game_over(self):
        return self._board.is_game_over()

    def legal_moves(self):
        return [move.uci() for move in self._board.legal_moves]

    def push(self, move):
        if isinstance(move, str):
            move = chess.Move.from_uci(move)
        self._board.push(move)
        return move

    def pop(self):
        return self._board.pop()

    def copy(self):
        clone = EngineBoard.__new__(EngineBoard)
        clone._board = self._board.copy()
        return clone

    def perft(self, depth):
        return _perft(self._board, depth)


def _perft(board, depth):
    if depth == 0:
        return 1
    if depth == 1:
        return board.legal_moves.count()
    nodes = 0
    for move in board.legal_moves:
        board.push(move)
        nodes += _perft(board, depth - 1)
        board.pop()
    return nodes
