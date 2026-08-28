from piece import Pawn, Knight, Bishop, Rook, Queen, King

_FEN_LETTER = {
    Pawn: 'p',
    Knight: 'n',
    Bishop: 'b',
    Rook: 'r',
    Queen: 'q',
    King: 'k',
}


def to_fen(board, turn, fullmove=1):
    rows = []
    for row in range(8):
        empty = 0
        line = []
        for col in range(8):
            piece = board.squares[row][col].piece
            if piece is None:
                empty += 1
                continue
            if empty:
                line.append(str(empty))
                empty = 0
            letter = _FEN_LETTER[type(piece)]
            line.append(letter.upper() if piece.color == 'white' else letter)
        if empty:
            line.append(str(empty))
        rows.append(''.join(line))

    castling = ''
    white_king = board.squares[7][4].piece
    if isinstance(white_king, King) and white_king.color == 'white' and not white_king.moved:
        rook = board.squares[7][7].piece
        if isinstance(rook, Rook) and rook.color == 'white' and not rook.moved:
            castling += 'K'
        rook = board.squares[7][0].piece
        if isinstance(rook, Rook) and rook.color == 'white' and not rook.moved:
            castling += 'Q'
    black_king = board.squares[0][4].piece
    if isinstance(black_king, King) and black_king.color == 'black' and not black_king.moved:
        rook = board.squares[0][7].piece
        if isinstance(rook, Rook) and rook.color == 'black' and not rook.moved:
            castling += 'k'
        rook = board.squares[0][0].piece
        if isinstance(rook, Rook) and rook.color == 'black' and not rook.moved:
            castling += 'q'

    ep = '-'
    for row in range(8):
        for col in range(8):
            piece = board.squares[row][col].piece
            if isinstance(piece, Pawn) and piece.en_passant:
                target_row = row - piece.dir
                ep = f"{'abcdefgh'[col]}{8 - target_row}"

    stm = 'w' if turn == 'white' else 'b'
    return f"{'/'.join(rows)} {stm} {castling or '-'} {ep} 0 {fullmove}"


def uci_to_rows(uci):
    from_col = ord(uci[0]) - ord('a')
    from_row = 8 - int(uci[1])
    to_col = ord(uci[2]) - ord('a')
    to_row = 8 - int(uci[3])
    promo = uci[4] if len(uci) > 4 else None
    return from_row, from_col, to_row, to_col, promo
