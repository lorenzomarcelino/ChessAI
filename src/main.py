import pygame
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game import Game, SIDEBAR_WIDTH, PADDING, PLAYER_BAR_HEIGHT
from square import Square
from move import Move
from menu import main_menu, draw_button
from display import Display
from move_notation import to_algebraic
from config import load_font, s, TEXT_WHITE
from fen import to_fen
from uci_move import apply_uci
from engine.skill import SKILL_ORDER
from engine.api import think


DRAG_THRESHOLD = s(6)


class Main:

    def __init__(self):
        pygame.init()
        self.display = Display()
        self.screen = self.display.screen
        self.game = None
        self._pointer_down = False
        self._drag_origin = None
        self._ai_pool = ThreadPoolExecutor(max_workers=1)
        self._ai_future = None
        self._ai_gen = 0
        self.update_dimensions()

    def update_dimensions(self):
        self.screen_width, self.screen_height = self.screen.get_size()
        bars_height = (PLAYER_BAR_HEIGHT + s(4)) * 2
        available_w = self.screen_width - SIDEBAR_WIDTH - PADDING * 3
        available_h = self.screen_height - PADDING * 2 - bars_height
        self.board_size = min(available_w, available_h, s(720))
        self.board_x = PADDING
        total_board_h = bars_height + self.board_size
        self.board_y = (self.screen_height - total_board_h) // 2 + PLAYER_BAR_HEIGHT + s(4)
        self.sidebar_x = self.board_x + self.board_size + PADDING
        self.sidebar_y = PADDING
        self.sidebar_w = max(s(200), self.screen_width - self.sidebar_x - PADDING)
        self.sidebar_h = self.screen_height - PADDING * 2
        self.cell_size = self.board_size // 8

    def draw_menu_button(self, surface):
        font = load_font(16, bold=True)
        button_rect = pygame.Rect(
            self.sidebar_x + self.sidebar_w - s(90),
            self.sidebar_y + s(12),
            s(74),
            s(32),
        )
        hovered = button_rect.collidepoint(pygame.mouse.get_pos())
        draw_button(surface, button_rect, 'Menu', font, hovered=hovered)
        return button_rect

    def render_frame(self, screen, game, board, dragger):
        game.show_background(screen)
        game.show_player_bars(screen, self.board_x, self.board_y, self.board_size)
        game.show_bg(screen, self.cell_size, self.board_x, self.board_y)
        game.show_last_move(screen, self.cell_size, self.board_x, self.board_y)
        game.show_selection(screen, self.cell_size, self.board_x, self.board_y)
        game.show_moves(screen, self.cell_size, self.board_x, self.board_y)
        game.show_pieces(screen, self.cell_size, self.board_x, self.board_y)
        game.show_sidebar(screen, self.sidebar_x, self.sidebar_y, self.sidebar_w, self.sidebar_h)

        if getattr(game, 'ai_thinking', False):
            think_font = load_font(18, bold=True)
            label = think_font.render('Pensando…', True, TEXT_WHITE)
            screen.blit(label, (self.sidebar_x + s(16), self.sidebar_y + self.sidebar_h - s(36)))

        menu_button = self.draw_menu_button(screen)

        if dragger.dragging:
            dragger.update_blit(screen, game.get_piece_image, self.cell_size)

        return menu_button

    def show_popup(self, message):
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        font = load_font(40, bold=True)
        text = font.render(message, True, (255, 80, 80))
        self.screen.blit(text, text.get_rect(center=(self.screen_width // 2, self.screen_height // 2)))
        pygame.display.flip()
        pygame.time.wait(3000)

    def _square_at(self, pos):
        x = pos[0] - self.board_x
        y = pos[1] - self.board_y
        board_px = self.cell_size * 8
        if not (0 <= x < board_px and 0 <= y < board_px):
            return None
        view_row = y // self.cell_size
        view_col = x // self.cell_size
        return self.game.board_pos(view_row, view_col)

    def _try_play_move(self, game, board, piece, initial_row, initial_col, final_row, final_col):
        if (initial_row, initial_col) == (final_row, final_col):
            return False, None
        move = Move(Square(initial_row, initial_col), Square(final_row, final_col))
        if not board.valid_move(piece, move):
            return False, None

        captured = board.squares[final_row][final_col].has_piece()
        notation = to_algebraic(board, piece, move)
        player = game.next_player
        board.move(piece, move)
        board.set_true_en_passant(piece)
        game.record_move(notation, player)
        game.on_move_played()
        game.play_sound(captured)
        game.next_turn()
        return True, game.check_game_over()

    def _finish_if_over(self, screen, game, board, dragger, result):
        if result == 'Checkmate':
            game.clock.stop()
            winner = 'Brancas' if game.next_player == 'black' else 'Pretas'
            self.render_frame(screen, game, board, dragger)
            self.show_popup(f'Xeque-mate! {winner} vencem!')
            return True
        if result == 'Stalemate':
            game.clock.stop()
            self.render_frame(screen, game, board, dragger)
            self.show_popup('Empate por afogamento!')
            return True
        return False

    def _select_own_piece(self, game, board, piece, row, col, pos):
        board.calc_moves(piece, row, col, bool=True)
        game.dragger.save_initial(row, col, self.cell_size)
        game.dragger.select_piece(piece, row, col)
        game.dragger.update_mouse(pos, self.cell_size, self.board_x, self.board_y)
        self._pointer_down = True
        self._drag_origin = pos

    def _cancel_ai(self):
        self._ai_gen += 1
        self._ai_future = None
        if self.game is not None:
            self.game.ai_thinking = False

    def _start_ai(self, game):
        fen = to_fen(game.board, game.next_player, fullmove=max(1, len(game.move_history)))
        skill = SKILL_ORDER[game.settings.ai_level]
        remaining_ms = None
        if game.settings.has_timer:
            remaining_ms = int(game.clock.get_time(game.next_player) * 1000)
        gen = self._ai_gen
        game.ai_thinking = True
        engine_kind = 'sf' if getattr(game.settings, 'opponent', 'ai') == 'ai_sf' else 'own'
        self._ai_future = (gen, self._ai_pool.submit(
            think, fen, skill=skill, remaining_ms=remaining_ms, engine_kind=engine_kind,
        ))

    def _poll_ai(self, screen, game, board, dragger):
        if self._ai_future is None:
            return False
        gen, future = self._ai_future
        if not future.done():
            return False
        self._ai_future = None
        game.ai_thinking = False
        if gen != self._ai_gen:
            return False
        uci = future.result()
        if not uci:
            return False
        played, result = apply_uci(game, uci)
        if played and self._finish_if_over(screen, game, board, dragger, result):
            return True
        return False

    def start_game(self, settings):
        self._cancel_ai()
        self.game = Game(settings)
        self.game.ai_thinking = False
        self.main_game_loop()

    def main_game_loop(self):
        screen = self.screen
        game = self.game
        board = self.game.board
        dragger = self.game.dragger

        running = True
        clock = pygame.time.Clock()
        self._pointer_down = False
        self._drag_origin = None

        while running:
            self.screen = self.display.screen
            screen = self.screen
            self.update_dimensions()

            if game.settings.has_timer:
                game.clock.tick(game.next_player)
                if game.clock.is_flagged(game.next_player):
                    game.clock.stop()
                    winner = 'Pretas' if game.next_player == 'white' else 'Brancas'
                    self.render_frame(screen, game, board, dragger)
                    self.show_popup(f'Tempo esgotado! {winner} vencem!')
                    return

            if game.is_ai_turn():
                if self._ai_future is None:
                    self._start_ai(game)
                elif self._poll_ai(screen, game, board, dragger):
                    return
                board = game.board
                dragger = game.dragger

            menu_button = self.render_frame(screen, game, board, dragger)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.VIDEORESIZE:
                    self.screen = self.display.on_resize(event.size)
                    screen = self.screen

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if menu_button.collidepoint(event.pos):
                        game.clock.stop()
                        self._cancel_ai()
                        running = False
                        break

                    if game.is_ai_turn():
                        continue

                    square = self._square_at(event.pos)
                    if square is None:
                        dragger.deselect()
                        continue

                    row, col = square
                    dragger.update_mouse(event.pos, self.cell_size, self.board_x, self.board_y)

                    if dragger.selected and dragger.piece is not None:
                        moved, result = self._try_play_move(
                            game, board, dragger.piece,
                            dragger.initial_row, dragger.initial_col, row, col,
                        )
                        if moved:
                            dragger.deselect()
                            if self._finish_if_over(screen, game, board, dragger, result):
                                return
                            continue

                    clicked = board.squares[row][col]
                    if clicked.has_piece() and clicked.piece.color == game.next_player:
                        self._select_own_piece(game, board, clicked.piece, row, col, event.pos)
                    else:
                        dragger.deselect()

                elif event.type == pygame.MOUSEMOTION:
                    dragger.update_mouse(event.pos, self.cell_size, self.board_x, self.board_y)
                    if self._pointer_down and dragger.selected and not dragger.dragging and self._drag_origin:
                        dx = event.pos[0] - self._drag_origin[0]
                        dy = event.pos[1] - self._drag_origin[1]
                        if dx * dx + dy * dy >= DRAG_THRESHOLD * DRAG_THRESHOLD:
                            dragger.start_drag()

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if dragger.dragging:
                        dragger.update_mouse(event.pos, self.cell_size, self.board_x, self.board_y)
                        square = self._square_at(event.pos)
                        moved = False
                        if square is not None:
                            row, col = square
                            played, result = self._try_play_move(
                                game, board, dragger.piece,
                                dragger.initial_row, dragger.initial_col, row, col,
                            )
                            if played:
                                moved = True
                                dragger.deselect()
                                if self._finish_if_over(screen, game, board, dragger, result):
                                    return
                        if not moved:
                            dragger.stop_drag()
                    self._pointer_down = False
                    self._drag_origin = None

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.screen = self.display.toggle_fullscreen()
                        screen = self.screen
                    elif event.key == pygame.K_r:
                        self._cancel_ai()
                        settings = game.settings
                        game.reset(settings)
                        game = self.game
                        game.ai_thinking = False
                        board = self.game.board
                        dragger = self.game.dragger
                        self._pointer_down = False
                        self._drag_origin = None

            pygame.display.update()
            clock.tick(60)


if __name__ == "__main__":
    main = Main()
    main_menu(main.screen, main.display, main.start_game)
    pygame.quit()
    sys.exit()
