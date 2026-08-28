"""Uso no PowerShell: python -m engine [profundidade]"""

import argparse

from engine.api import think


def main():
    parser = argparse.ArgumentParser(description='Engine clássica do ChessAI (Fase 1, sem treino).')
    parser.add_argument('depth', nargs='?', type=int, default=4, help='profundidade da busca (padrão: 4)')
    parser.add_argument('--fen', default=None, help='posição FEN; omite para a posição inicial')
    args = parser.parse_args()
    move = think(fen=args.fen, depth=args.depth)
    print(move)


if __name__ == '__main__':
    main()
