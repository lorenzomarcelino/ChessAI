import pygame
from const import *
from board import Board
from dragger import Dragger
from config import Config
from square import Square

class Game:

    def __init__(self):
        self.next_player = 'white'
        self.hovered_sqr = None
        self.board = Board()
        self.dragger = Dragger()
        self.config = Config()

    def show_bg(self, surface, cell_size, border_width, border_height):
        theme = self.config.theme
        
        for row in range(ROWS):
            for col in range(COLS):
                color = theme.bg.light if (row + col) % 2 == 0 else theme.bg.dark
                rect = (border_width + col * cell_size, border_height + row * cell_size, cell_size, cell_size)
                pygame.draw.rect(surface, color, rect)

                if col == 0:
                    color = theme.bg.dark if row % 2 == 0 else theme.bg.light
                    lbl = self.config.font.render(str(ROWS-row), 1, color)
                    lbl_pos = (border_width + 5, border_height + 5 + row * cell_size)
                    surface.blit(lbl, lbl_pos)

                if row == 7:
                    color = theme.bg.dark if (row + col) % 2 == 0 else theme.bg.light
                    lbl = self.config.font.render(Square.get_alphacol(col), 1, color)
                    lbl_pos = (border_width + col * cell_size + cell_size - 20, border_height + cell_size * 8 - 20)
                    surface.blit(lbl, lbl_pos)

    def show_pieces(self, surface, cell_size, border_width, border_height):
        for row in range(ROWS):
            for col in range(COLS):
                if self.board.squares[row][col].has_piece():
                    piece = self.board.squares[row][col].piece
                    if piece is not self.dragger.piece:
                        piece.set_texture(size=80)  # Tamanho das imagens ajustado para 80px
                        img = pygame.image.load(piece.texture)
                        img_center = border_width + col * cell_size + cell_size // 2, border_height + row * cell_size + cell_size // 2
                        piece.texture_rect = img.get_rect(center=img_center)
                        surface.blit(img, piece.texture_rect)

    def show_moves(self, surface, cell_size, border_width, border_height):
        theme = self.config.theme

        if self.dragger.dragging:
            piece = self.dragger.piece

            for move in piece.moves:
                color = theme.moves.light if (move.final.row + move.final.col) % 2 == 0 else theme.moves.dark
                rect = (border_width + move.final.col * cell_size, border_height + move.final.row * cell_size, cell_size, cell_size)
                pygame.draw.rect(surface, color, rect)

    def show_last_move(self, surface, cell_size, border_width, border_height):
        theme = self.config.theme

        if self.board.last_move:
            initial = self.board.last_move.initial
            final = self.board.last_move.final

            for pos in [initial, final]:
                color = theme.trace.light if (pos.row + pos.col) % 2 == 0 else theme.trace.dark
                rect = (border_width + pos.col * cell_size, border_height + pos.row * cell_size, cell_size, cell_size)
                pygame.draw.rect(surface, color, rect)

    def show_hover(self, surface, cell_size, border_width, border_height):
        if self.hovered_sqr:
            color = (180, 180, 180)
            rect = (border_width + self.hovered_sqr.col * cell_size, border_height + self.hovered_sqr.row * cell_size, cell_size, cell_size)
            pygame.draw.rect(surface, color, rect, width=3)

    def next_turn(self):
        self.next_player = 'white' if self.next_player == 'black' else 'black'

    def set_hover(self, row, col):
        self.hovered_sqr = self.board.squares[row][col]

    def change_theme(self):
        self.config.change_theme()

    def play_sound(self, captured=False):
        if captured:
            self.config.capture_sound.play()
        else:
            self.config.move_sound.play()

    def reset(self):
        self.__init__()

    def check_game_over(self):
        if self.is_checkmate():
            return "Checkmate"
        if self.is_stalemate():
            return "Stalemate"
        return None

    def is_checkmate(self):
        king = self.get_king(self.next_player)
        if king is None:
            return False

        for row in range(ROWS):
            for col in range(COLS):
                if self.board.squares[row][col].has_team_piece(king.color):
                    piece = self.board.squares[row][col].piece
                    self.board.calc_moves(piece, row, col, bool=False)
                    for move in piece.moves:
                        if not self.board.would_be_in_check(piece, move):
                            return False
        return self.board.in_check(king.color)

    def is_stalemate(self):
        king = self.get_king(self.next_player)
        if king is None:
            return False

        for row in range(ROWS):
            for col in range(COLS):
                if self.board.squares[row][col].has_team_piece(king.color):
                    piece = self.board.squares[row][col].piece
                    self.board.calc_moves(piece, row, col, bool=False)
                    for move in piece.moves:
                        if not self.board.would_be_in_check(piece, move):
                            return False
        return not self.board.in_check(king.color)

    def get_king(self, color):
        return self.board.get_king(color)
