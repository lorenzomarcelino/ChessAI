import pytest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from board import Board
from square import Square
from move import Move
from piece import Pawn, Knight


def test_en_passant_flag_after_two_square_move():
    board = Board()
    pawn = board.squares[6][4].piece  # white pawn at e2
    move = Move(Square(6, 4), Square(4, 4))
    board.move(pawn, move)
    board.set_true_en_passant(pawn, move.initial, move.final)
    assert pawn.en_passant
    # ensure others cleared
    other_pawn = board.squares[6][3].piece
    assert not other_pawn.en_passant


def test_en_passant_not_set_for_one_square_move():
    board = Board()
    pawn = board.squares[6][4].piece
    move = Move(Square(6, 4), Square(5, 4))
    board.move(pawn, move)
    board.set_true_en_passant(pawn, move.initial, move.final)
    assert not pawn.en_passant


def test_en_passant_cleared_after_non_pawn_move():
    board = Board()
    pawn = board.squares[6][4].piece
    pawn_move = Move(Square(6, 4), Square(4, 4))
    board.move(pawn, pawn_move)
    board.set_true_en_passant(pawn, pawn_move.initial, pawn_move.final)
    assert pawn.en_passant

    knight = board.squares[7][1].piece
    knight_move = Move(Square(7, 1), Square(5, 2))
    board.move(knight, knight_move)
    board.set_true_en_passant(knight, knight_move.initial, knight_move.final)
    assert not pawn.en_passant
