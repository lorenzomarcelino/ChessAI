from square import Square
from move import Move
from fen import uci_to_rows
from move_notation import to_algebraic


def apply_uci(game, uci):
    board = game.board
    from_row, from_col, to_row, to_col, _promo = uci_to_rows(uci)
    square = board.squares[from_row][from_col]
    if not square.has_piece():
        return False, None
    piece = square.piece
    board.calc_moves(piece, from_row, from_col, bool=True)
    move = Move(Square(from_row, from_col), Square(to_row, to_col))
    if not board.valid_move(piece, move):
        return False, None

    captured = board.squares[to_row][to_col].has_piece()
    notation = to_algebraic(board, piece, move)
    player = game.next_player
    board.move(piece, move)
    board.set_true_en_passant(piece)
    game.record_move(notation, player)
    game.on_move_played()
    game.play_sound(captured)
    game.next_turn()
    return True, game.check_game_over()
