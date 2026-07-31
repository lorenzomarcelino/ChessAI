from piece import Pawn, Knight, Bishop, Rook, Queen, King
from square import Square

PIECE_SYMBOLS = {
    Knight: 'N',
    Bishop: 'B',
    Rook: 'R',
    Queen: 'Q',
    King: 'K',
}


def _square_name(row, col):
    return f"{Square.get_alphacol(col)}{8 - row}"


def to_algebraic(board, piece, move):
    initial = move.initial
    final = move.final
    dest = _square_name(final.row, final.col)

    if isinstance(piece, King) and abs(final.col - initial.col) == 2:
        return 'O-O-O' if final.col < initial.col else 'O-O'

    captured = board.squares[final.row][final.col].has_piece()
    en_passant = (
        isinstance(piece, Pawn)
        and final.col != initial.col
        and not captured
    )

    if isinstance(piece, Pawn):
        notation = ''
        if captured or en_passant:
            notation += f"{Square.get_alphacol(initial.col)}x"
        notation += dest
        if final.row in (0, 7):
            notation += '=Q'
        return notation

    symbol = PIECE_SYMBOLS.get(type(piece), '')
    notation = symbol

    ambiguous_from = []
    for row in range(8):
        for col in range(8):
            square = board.squares[row][col]
            if not square.has_piece() or square.piece.color != piece.color:
                continue
            other = square.piece
            if type(other) is not type(piece):
                continue
            board.calc_moves(other, row, col, bool=False)
            for other_move in other.moves:
                if other_move.final.row == final.row and other_move.final.col == final.col:
                    ambiguous_from.append((row, col))
                    break

    if len(ambiguous_from) > 1:
        files = {Square.get_alphacol(col) for row, col in ambiguous_from}
        ranks = {str(8 - row) for row, col in ambiguous_from}
        if len(files) > 1:
            notation += Square.get_alphacol(initial.col)
        elif len(ranks) > 1:
            notation += str(8 - initial.row)
        else:
            notation += Square.get_alphacol(initial.col) + str(8 - initial.row)

    if captured or en_passant:
        notation += 'x'

    notation += dest
    return notation
