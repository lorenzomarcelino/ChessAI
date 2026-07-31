import pygame
import sys

from game import Game, SIDEBAR_WIDTH, PADDING, PLAYER_BAR_HEIGHT
from square import Square
from move import Move
from menu import main_menu
from display import Display
from move_notation import to_algebraic


class Main:

    def __init__(self):
        pygame.init()
        self.display = Display()
        self.screen = self.display.screen
        self.game = None
        self.update_dimensions()

    def update_dimensions(self):
        self.screen_width, self.screen_height = self.screen.get_size()
        bars_height = (PLAYER_BAR_HEIGHT + 4) * 2
        available_w = self.screen_width - SIDEBAR_WIDTH - PADDING * 3
        available_h = self.screen_height - PADDING * 2 - bars_height
        self.board_size = min(available_w, available_h, 720)
        self.board_x = PADDING
        total_board_h = bars_height + self.board_size
        self.board_y = (self.screen_height - total_board_h) // 2 + PLAYER_BAR_HEIGHT + 4
        self.sidebar_x = self.board_x + self.board_size + PADDING
        self.sidebar_y = PADDING
        self.sidebar_w = max(200, self.screen_width - self.sidebar_x - PADDING)
        self.sidebar_h = self.screen_height - PADDING * 2
        self.cell_size = self.board_size // 8

    def draw_menu_button(self, surface):
        font = pygame.font.Font(None, 28)
        button_rect = pygame.Rect(self.sidebar_x + self.sidebar_w - 90, self.sidebar_y + 12, 74, 32)
        pygame.draw.rect(surface, (90, 87, 84), button_rect, border_radius=4)
        text = font.render('Menu', True, (230, 230, 230))
        surface.blit(text, text.get_rect(center=button_rect.center))
        return button_rect

    def render_frame(self, screen, game, board, dragger):
        game.show_background(screen)
        game.show_player_bars(screen, self.board_x, self.board_y, self.board_size)
        game.show_bg(screen, self.cell_size, self.board_x, self.board_y)
        game.show_last_move(screen, self.cell_size, self.board_x, self.board_y)
        game.show_moves(screen, self.cell_size, self.board_x, self.board_y)
        game.show_pieces(screen, self.cell_size, self.board_x, self.board_y)
        game.show_sidebar(screen, self.sidebar_x, self.sidebar_y, self.sidebar_w, self.sidebar_h)

        menu_button = self.draw_menu_button(screen)

        if dragger.dragging:
            dragger.update_blit(screen, game.get_piece_image, self.cell_size)

        return menu_button

    def show_popup(self, message):
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        font = pygame.font.Font(None, 56)
        text = font.render(message, True, (255, 80, 80))
        self.screen.blit(text, text.get_rect(center=(self.screen_width // 2, self.screen_height // 2)))
        pygame.display.flip()
        pygame.time.wait(3000)

    def _is_on_board(self, x, y):
        return 0 <= x < self.board_size and 0 <= y < self.board_size

    def start_game(self, settings):
        self.game = Game(settings)
        self.main_game_loop()

    def main_game_loop(self):
        screen = self.screen
        game = self.game
        board = self.game.board
        dragger = self.game.dragger

        running = True
        clock = pygame.time.Clock()

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

            menu_button = self.render_frame(screen, game, board, dragger)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.VIDEORESIZE:
                    self.screen = self.display.on_resize(event.size)
                    screen = self.screen

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    dragger.update_mouse(event.pos, self.cell_size, self.board_x, self.board_y)

                    if self._is_on_board(dragger.mouseX, dragger.mouseY):
                        clicked_row = dragger.mouseY // self.cell_size
                        clicked_col = dragger.mouseX // self.cell_size

                        if board.squares[clicked_row][clicked_col].has_piece():
                            piece = board.squares[clicked_row][clicked_col].piece
                            if piece.color == game.next_player:
                                board.calc_moves(piece, clicked_row, clicked_col, bool=True)
                                dragger.save_initial(event.pos, self.cell_size, self.board_x, self.board_y)
                                dragger.drag_piece(piece)

                    if menu_button.collidepoint(event.pos):
                        game.clock.stop()
                        running = False

                elif event.type == pygame.MOUSEMOTION:
                    if dragger.dragging:
                        dragger.update_mouse(event.pos, self.cell_size, self.board_x, self.board_y)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragger.dragging:
                        dragger.update_mouse(event.pos, self.cell_size, self.board_x, self.board_y)

                        if self._is_on_board(dragger.mouseX, dragger.mouseY):
                            released_row = dragger.mouseY // self.cell_size
                            released_col = dragger.mouseX // self.cell_size

                            initial = Square(dragger.initial_row, dragger.initial_col)
                            final = Square(released_row, released_col)
                            move = Move(initial, final)

                            if board.valid_move(dragger.piece, move):
                                captured = board.squares[released_row][released_col].has_piece()
                                notation = to_algebraic(board, dragger.piece, move)
                                player = game.next_player
                                board.move(dragger.piece, move)
                                board.set_true_en_passant(dragger.piece)
                                game.record_move(notation, player)
                                game.on_move_played()
                                game.play_sound(captured)
                                game.next_turn()

                                game_over = game.check_game_over()
                                if game_over == "Checkmate":
                                    game.clock.stop()
                                    winner = 'Brancas' if game.next_player == 'black' else 'Pretas'
                                    self.render_frame(screen, game, board, dragger)
                                    self.show_popup(f'Xeque-mate! {winner} vencem!')
                                    return
                                elif game_over == "Stalemate":
                                    game.clock.stop()
                                    self.render_frame(screen, game, board, dragger)
                                    self.show_popup('Empate por afogamento!')
                                    return

                        dragger.undrag_piece()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.screen = self.display.toggle_fullscreen()
                        screen = self.screen
                    elif event.key == pygame.K_r:
                        settings = game.settings
                        game.reset(settings)
                        game = self.game
                        board = self.game.board
                        dragger = self.game.dragger

            pygame.display.update()
            clock.tick(60)


if __name__ == "__main__":
    main = Main()
    main_menu(main.screen, main.display, main.start_game)
    pygame.quit()
    sys.exit()
