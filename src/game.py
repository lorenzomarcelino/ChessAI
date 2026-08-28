import pygame
from const import *
from board import Board
from dragger import Dragger
from config import (
    Config, APP_BG, SIDEBAR_BG, SIDEBAR_TEXT, SIDEBAR_MUTED, SIDEBAR_HIGHLIGHT,
    PLAYER_BAR_BG, TIMER_INACTIVE_BG, TIMER_INACTIVE_TEXT,
    TIMER_ACTIVE_BG, TIMER_ACTIVE_TEXT, s,
)
from square import Square
from chess_clock import ChessClock
from settings import GameSettings

SIDEBAR_WIDTH = s(280)
PADDING = s(20)
PLAYER_BAR_HEIGHT = s(44)
TIMER_WIDTH = s(76)
TIMER_HEIGHT = s(34)


class Game:

    def __init__(self, settings=None):
        self.settings = settings or GameSettings()
        self.next_player = 'white'
        self.hovered_sqr = None
        self.board = Board()
        self.dragger = Dragger()
        self.config = Config(theme_idx=self.settings.theme_idx)
        self.move_history = []
        self._image_cache = {}
        self.clock = ChessClock(
            self.settings.time_per_player,
            enabled=self.settings.has_timer,
        )
        self._game_started = False
        self.bottom_color = self.settings.resolve_bottom_color()
        self.ai_thinking = False

    def is_ai_turn(self):
        if getattr(self.settings, 'opponent', 'human') not in ('ai', 'ai_sf'):
            return False
        return self.next_player != self.bottom_color

    def view_pos(self, row, col):
        if self.bottom_color == 'black':
            return 7 - row, 7 - col
        return row, col

    def board_pos(self, view_row, view_col):
        return self.view_pos(view_row, view_col)

    def square_xy(self, row, col, cell_size, board_x, board_y):
        view_row, view_col = self.view_pos(row, col)
        return board_x + view_col * cell_size, board_y + view_row * cell_size

    def record_move(self, notation, color):
        if color == 'white':
            self.move_history.append({
                'number': len(self.move_history) + 1,
                'white': notation,
                'black': None,
            })
        elif self.move_history:
            self.move_history[-1]['black'] = notation

    def on_move_played(self):
        if not self._game_started and self.settings.has_timer:
            self._game_started = True
            self.clock.start()

    def get_piece_image(self, piece, size):
        piece.set_texture(size=128)
        key = (piece.texture, size)
        if key not in self._image_cache:
            img = pygame.image.load(piece.texture).convert_alpha()
            self._image_cache[key] = pygame.transform.smoothscale(img, (size, size))
        return self._image_cache[key]

    def show_background(self, surface):
        surface.fill(APP_BG)

    def show_bg(self, surface, cell_size, board_x, board_y):
        theme = self.config.theme

        for row in range(ROWS):
            for col in range(COLS):
                color = theme.bg.light if (row + col) % 2 == 0 else theme.bg.dark
                x, y = self.square_xy(row, col, cell_size, board_x, board_y)
                pygame.draw.rect(surface, color, (x, y, cell_size, cell_size))

                view_row, view_col = self.view_pos(row, col)
                if view_col == 0:
                    coord_color = theme.bg.dark if (row + col) % 2 == 0 else theme.bg.light
                    lbl = self.config.font.render(str(ROWS - row), True, coord_color)
                    surface.blit(lbl, (x + s(5), y + s(4)))

                if view_row == 7:
                    coord_color = theme.bg.dark if (row + col) % 2 == 0 else theme.bg.light
                    lbl = self.config.font.render(Square.get_alphacol(col), True, coord_color)
                    surface.blit(lbl, (
                        x + cell_size - lbl.get_width() - s(5),
                        y + cell_size - lbl.get_height() - s(4),
                    ))

    def show_pieces(self, surface, cell_size, board_x, board_y):
        piece_size = int(cell_size * 0.88)
        for row in range(ROWS):
            for col in range(COLS):
                if self.board.squares[row][col].has_piece():
                    piece = self.board.squares[row][col].piece
                    if self.dragger.dragging and piece is self.dragger.piece:
                        continue
                    img = self.get_piece_image(piece, piece_size)
                    x, y = self.square_xy(row, col, cell_size, board_x, board_y)
                    center = (x + cell_size // 2, y + cell_size // 2)
                    rect = img.get_rect(center=center)
                    surface.blit(img, rect)

    def show_selection(self, surface, cell_size, board_x, board_y):
        if not self.dragger.selected:
            return
        row, col = self.dragger.initial_row, self.dragger.initial_col
        overlay = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
        overlay.fill((246, 246, 105, 90))
        x, y = self.square_xy(row, col, cell_size, board_x, board_y)
        surface.blit(overlay, (x, y))

    def show_moves(self, surface, cell_size, board_x, board_y):
        if not self.dragger.selected or self.dragger.piece is None:
            return

        piece = self.dragger.piece
        for move in piece.moves:
            x, y = self.square_xy(move.final.row, move.final.col, cell_size, board_x, board_y)
            cx = x + cell_size // 2
            cy = y + cell_size // 2
            target = self.board.squares[move.final.row][move.final.col]
            radius = max(s(4), cell_size // 8)
            if target.has_enemy_piece(piece.color):
                pygame.draw.circle(surface, (40, 40, 40), (cx, cy), cell_size // 2 - s(4), s(3))
            else:
                pygame.draw.circle(surface, (40, 40, 40), (cx, cy), radius)

    def show_last_move(self, surface, cell_size, board_x, board_y):
        theme = self.config.theme

        if self.board.last_move:
            initial = self.board.last_move.initial
            final = self.board.last_move.final

            for pos in [initial, final]:
                color = theme.trace.light if (pos.row + pos.col) % 2 == 0 else theme.trace.dark
                x, y = self.square_xy(pos.row, pos.col, cell_size, board_x, board_y)
                pygame.draw.rect(surface, color, (x, y, cell_size, cell_size))

    def _draw_timer(self, surface, x, y, time_seconds, active):
        rect = pygame.Rect(x, y, TIMER_WIDTH, TIMER_HEIGHT)
        bg = TIMER_ACTIVE_BG if active else TIMER_INACTIVE_BG
        text_color = TIMER_ACTIVE_TEXT if active else TIMER_INACTIVE_TEXT
        pygame.draw.rect(surface, bg, rect, border_radius=s(4))

        time_str = ChessClock.format_time(time_seconds)
        font = self.config.timer_font_active if active else self.config.timer_font
        text = font.render(time_str, True, text_color)
        surface.blit(text, text.get_rect(center=rect.center))

    def _draw_player_bar(self, surface, board_x, board_y, board_w, color, name, active):
        bar_rect = pygame.Rect(board_x, board_y, board_w, PLAYER_BAR_HEIGHT)
        pygame.draw.rect(surface, PLAYER_BAR_BG, bar_rect, border_radius=s(4))

        avatar_size = s(30)
        avatar_x = board_x + s(8)
        avatar_y = board_y + (PLAYER_BAR_HEIGHT - avatar_size) // 2
        avatar_color = (220, 220, 220) if color == 'white' else (60, 60, 60)
        pygame.draw.rect(surface, avatar_color, (avatar_x, avatar_y, avatar_size, avatar_size), border_radius=s(3))

        name_text = self.config.player_font.render(name, True, SIDEBAR_TEXT)
        surface.blit(name_text, (avatar_x + avatar_size + s(10), board_y + (PLAYER_BAR_HEIGHT - name_text.get_height()) // 2))

        if self.settings.has_timer:
            time_seconds = self.clock.get_time(color)
            timer_x = board_x + board_w - TIMER_WIDTH - s(8)
            timer_y = board_y + (PLAYER_BAR_HEIGHT - TIMER_HEIGHT) // 2
            self._draw_timer(surface, timer_x, timer_y, time_seconds, active)

    def show_player_bars(self, surface, board_x, board_y, board_size):
        top_bar_y = board_y - PLAYER_BAR_HEIGHT - s(4)
        bottom_bar_y = board_y + board_size + s(4)

        top_color = 'white' if self.bottom_color == 'black' else 'black'
        bottom_color = self.bottom_color
        names = {'white': 'Brancas', 'black': 'Pretas'}

        self._draw_player_bar(
            surface, board_x, top_bar_y, board_size,
            top_color, names[top_color], self.next_player == top_color,
        )
        self._draw_player_bar(
            surface, board_x, bottom_bar_y, board_size,
            bottom_color, names[bottom_color], self.next_player == bottom_color,
        )

    def show_sidebar(self, surface, sidebar_x, sidebar_y, sidebar_w, sidebar_h):
        sidebar_rect = pygame.Rect(sidebar_x, sidebar_y, sidebar_w, sidebar_h)
        pygame.draw.rect(surface, SIDEBAR_BG, sidebar_rect, border_radius=s(4))

        title = self.config.sidebar_title_font.render('Lances', True, SIDEBAR_TEXT)
        surface.blit(title, (sidebar_x + s(16), sidebar_y + s(16)))

        if self.settings.has_timer:
            mode = self.config.sidebar_font.render(self.settings.time_label, True, SIDEBAR_MUTED)
            surface.blit(mode, (sidebar_x + s(16), sidebar_y + s(42)))

        y = sidebar_y + s(70) if self.settings.has_timer else sidebar_y + s(56)
        row_height = s(28)
        col_number = sidebar_x + s(16)
        col_white = sidebar_x + s(56)
        col_black = sidebar_x + s(140)

        header_font = self.config.sidebar_font
        surface.blit(header_font.render('#', True, SIDEBAR_MUTED), (col_number, y))
        surface.blit(header_font.render('Brancas', True, SIDEBAR_MUTED), (col_white, y))
        surface.blit(header_font.render('Pretas', True, SIDEBAR_MUTED), (col_black, y))
        y += row_height + s(4)

        font = self.config.sidebar_font
        visible_rows = max(1, (sidebar_h - s(100)) // row_height)

        if len(self.move_history) > visible_rows:
            history_slice = self.move_history[-visible_rows:]
        else:
            history_slice = self.move_history

        for entry in history_slice:
            is_last = entry is self.move_history[-1] if self.move_history else False
            if is_last:
                highlight = pygame.Rect(sidebar_x + s(8), y - s(2), sidebar_w - s(16), row_height)
                pygame.draw.rect(surface, SIDEBAR_HIGHLIGHT, highlight, border_radius=s(3))

            surface.blit(font.render(str(entry['number']) + '.', True, SIDEBAR_MUTED), (col_number, y))
            surface.blit(font.render(entry['white'] or '', True, SIDEBAR_TEXT), (col_white, y))
            surface.blit(font.render(entry['black'] or '', True, SIDEBAR_TEXT), (col_black, y))
            y += row_height

    def next_turn(self):
        self.next_player = 'white' if self.next_player == 'black' else 'black'

    def change_theme(self):
        self.config.change_theme()

    def play_sound(self, captured=False):
        if captured:
            self.config.capture_sound.play()
        else:
            self.config.move_sound.play()

    def reset(self, settings=None):
        self.__init__(settings or self.settings)

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
