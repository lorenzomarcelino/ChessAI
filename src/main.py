import pygame
import sys

from const import *
from game import Game
from square import Square
from move import Move
from menu import main_menu

class Main:

    def __init__(self):
        pygame.init()
        info = pygame.display.Info()
        self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
        pygame.display.set_caption('Chess')
        self.board_size = 600  # Tamanho fixo para o tabuleiro
        self.update_dimensions()
        self.game = Game()

    def update_dimensions(self):
        self.screen_width, self.screen_height = self.screen.get_size()
        self.cell_size = self.board_size // 8
        self.border_width = (self.screen_width - self.board_size) // 2
        self.border_height = (self.screen_height - self.board_size) // 2

    def draw_buttons(self):
        font = pygame.font.Font(None, 36)
        button_color = (255, 0, 0)
        text_color = (255, 255, 255)
        button_rect = pygame.Rect(self.screen_width - 150, 20, 100, 50)
        pygame.draw.rect(self.screen, button_color, button_rect)
        text_surface = font.render("Menu", True, text_color)
        text_rect = text_surface.get_rect(center=button_rect.center)
        self.screen.blit(text_surface, text_rect)
        return button_rect

    def show_popup(self, message):
        font = pygame.font.Font(None, 74)
        text_color = (255, 0, 0)
        text_surface = font.render(message, True, text_color)
        text_rect = text_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(text_surface, text_rect)
        pygame.display.flip()
        pygame.time.wait(3000)

    def main_game_loop(self):
        
        screen = self.screen
        game = self.game
        board = self.game.board
        dragger = self.game.dragger

        running = True
        while running:
            self.update_dimensions()

            # show methods
            game.show_bg(screen, self.cell_size, self.border_width, self.border_height)
            game.show_last_move(screen, self.cell_size, self.border_width, self.border_height)
            game.show_moves(screen, self.cell_size, self.border_width, self.border_height)
            game.show_pieces(screen, self.cell_size, self.border_width, self.border_height)
            game.show_hover(screen, self.cell_size, self.border_width, self.border_height)
            
            # Draw buttons
            menu_button = self.draw_buttons()

            if dragger.dragging:
                dragger.update_blit(screen, self.cell_size, self.border_width, self.border_height)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # click
                if event.type == pygame.MOUSEBUTTONDOWN:
                    dragger.update_mouse(event.pos, self.cell_size, self.border_width, self.border_height)

                    if dragger.mouseX < self.board_size and dragger.mouseY < self.board_size:
                        clicked_row = dragger.mouseY // self.cell_size
                        clicked_col = dragger.mouseX // self.cell_size

                        # if clicked square has a piece ?
                        if board.squares[clicked_row][clicked_col].has_piece():
                            piece = board.squares[clicked_row][clicked_col].piece
                            # valid piece (color) ?
                            if piece.color == game.next_player:
                                board.calc_moves(piece, clicked_row, clicked_col, bool=True)
                                dragger.save_initial(event.pos, self.cell_size, self.border_width, self.border_height)
                                dragger.drag_piece(piece)
                                # show methods 
                                game.show_bg(screen, self.cell_size, self.border_width, self.border_height)
                                game.show_last_move(screen, self.cell_size, self.border_width, self.border_height)
                                game.show_moves(screen, self.cell_size, self.border_width, self.border_height)
                                game.show_pieces(screen, self.cell_size, self.border_width, self.border_height)

                    # Check if menu button is clicked
                    if menu_button.collidepoint(event.pos):
                        running = False
                
                # mouse motion
                elif event.type == pygame.MOUSEMOTION:
                    if dragger.dragging:
                        dragger.update_mouse(event.pos, self.cell_size, self.border_width, self.border_height)
                        # show methods
                        game.show_bg(screen, self.cell_size, self.border_width, self.border_height)
                        game.show_last_move(screen, self.cell_size, self.border_width, self.border_height)
                        game.show_moves(screen, self.cell_size, self.border_width, self.border_height)
                        game.show_pieces(screen, self.cell_size, self.border_width, self.border_height)
                        game.show_hover(screen, self.cell_size, self.border_width, self.border_height)
                        dragger.update_blit(screen, self.cell_size, self.border_width, self.border_height)
                
                # click release
                elif event.type == pygame.MOUSEBUTTONUP:
                    
                    if dragger.dragging:
                        dragger.update_mouse(event.pos, self.cell_size, self.border_width, self.border_height)

                        if dragger.mouseX < self.board_size and dragger.mouseY < self.board_size:
                            released_row = dragger.mouseY // self.cell_size
                            released_col = dragger.mouseX // self.cell_size

                            # create possible move
                            initial = Square(dragger.initial_row, dragger.initial_col)
                            final = Square(released_row, released_col)
                            move = Move(initial, final)

                            # valid move ?
                            if board.valid_move(dragger.piece, move):
                                # normal capture
                                captured = board.squares[released_row][released_col].has_piece()
                                board.move(dragger.piece, move)

                                board.set_true_en_passant(dragger.piece)                            

                                # sounds
                                game.play_sound(captured)
                                # show methods
                                game.show_bg(screen, self.cell_size, self.border_width, self.border_height)
                                game.show_last_move(screen, self.cell_size, self.border_width, self.border_height)
                                game.show_pieces(screen, self.cell_size, self.border_width, self.border_height)
                                # next turn
                                game.next_turn()

                                game_over = game.check_game_over()
                                if game_over == "Checkmate":
                                    winner = "White" if game.next_player == 'black' else "Black"
                                    self.show_popup(f"Checkmate! {winner} wins!")
                                    running = False
                                elif game_over == "Stalemate":
                                    self.show_popup("Stalemate! It's a draw!")
                                    running = False
                            
                        dragger.undrag_piece()
                
                # key press
                elif event.type == pygame.KEYDOWN:
                    
                    # changing themes
                    if event.key == pygame.K_t:
                        game.change_theme()

                    # resetting game
                    if event.key == pygame.K_r:
                        game.reset()
                        game = self.game
                        board = self.game.board
                        dragger = self.game.dragger

            pygame.display.update()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main = Main()
    main_menu(main.main_game_loop)
