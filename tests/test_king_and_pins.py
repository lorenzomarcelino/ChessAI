import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from board import Board
from piece import King, Rook


def setup_empty_board():
    board = Board()
    for r in range(8):
        for c in range(8):
            board.squares[r][c].piece = None
    return board


def test_castling_blocked_by_attack():
    board = setup_empty_board()

    # place kings and rooks for castling
    white_king = King('white')
    white_rook = Rook('white')
    board.squares[7][4].piece = white_king
    board.squares[7][7].piece = white_rook

    black_king = King('black')
    board.squares[0][4].piece = black_king

    # black rook attacking f1
    attacking_rook = Rook('black')
    board.squares[3][5].piece = attacking_rook

    # clear column f between rook and f1
    for r in range(4,7):
        board.squares[r][5].piece = None

    board.calc_moves(white_king, 7, 4)
    castles = [(m.final.row, m.final.col) for m in white_king.moves]
    assert (7, 6) not in castles


def test_pinned_piece_has_no_legal_moves():
    board = setup_empty_board()

    board.squares[7][4].piece = King('white')
    pinned_rook = Rook('white')
    board.squares[6][4].piece = pinned_rook
    board.squares[0][4].piece = Rook('black')
    board.squares[0][0].piece = King('black')

    board.calc_moves(pinned_rook, 6, 4)
    allowed = [(m.final.row, m.final.col) for m in pinned_rook.moves]
    assert allowed == [(5, 4), (4, 4), (3, 4), (2, 4), (1, 4), (0, 4)]
