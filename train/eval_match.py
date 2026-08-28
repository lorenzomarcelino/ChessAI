"""Match engine vs engine (Fase 3.4 / 5)."""

import argparse

from engine.board import EngineBoard
from engine.api import think


def play_match(skill_a, skill_b, games=4, depth_a=None, depth_b=None, max_plies=80):
    wins = {'a': 0, 'b': 0, 'draw': 0}
    for i in range(games):
        a_is_white = i % 2 == 0
        board = EngineBoard()
        plies = 0
        while not board.is_game_over and plies < max_plies:
            white_turn = board.turn == 'white'
            use_a = white_turn == a_is_white
            move = think(
                board.to_fen(),
                skill=skill_a if use_a else skill_b,
                depth=depth_a if use_a else depth_b,
            )
            if move is None:
                break
            board.push(move)
            plies += 1
        if board.is_checkmate:
            winner_white = board.turn == 'black'
            a_won = winner_white == a_is_white
            wins['a' if a_won else 'b'] += 1
        else:
            wins['draw'] += 1
        print(f'jogo {i + 1}: {wins}')
    return wins


def main():
    parser = argparse.ArgumentParser(description='Match entre dois níveis/configurações.')
    parser.add_argument('--a', default='mestre')
    parser.add_argument('--b', default='iniciante')
    parser.add_argument('--games', type=int, default=4)
    args = parser.parse_args()
    result = play_match(args.a, args.b, games=args.games)
    print(result)


if __name__ == '__main__':
    main()
