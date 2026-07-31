import pygame

class Dragger:

    def __init__(self):
        self.piece = None
        self.dragging = False
        self.mouseX = 0
        self.mouseY = 0
        self.screen_x = 0
        self.screen_y = 0
        self.initial_row = 0
        self.initial_col = 0
        self.cell_size = 0

    def update_mouse(self, pos, cell_size, board_x, board_y):
        self.screen_x, self.screen_y = pos
        self.mouseX = pos[0] - board_x
        self.mouseY = pos[1] - board_y

    def save_initial(self, pos, cell_size, board_x, board_y):
        self.cell_size = cell_size
        self.initial_row = (pos[1] - board_y) // cell_size
        self.initial_col = (pos[0] - board_x) // cell_size

    def drag_piece(self, piece):
        self.piece = piece
        self.dragging = True

    def undrag_piece(self):
        self.piece = None
        self.dragging = False

    def update_blit(self, surface, get_piece_image, cell_size):
        piece_size = int(cell_size * 0.95)
        self.piece.set_texture(size=80)
        texture = get_piece_image(self.piece, piece_size)
        self.piece.texture_rect = texture.get_rect(center=(self.screen_x, self.screen_y))
        surface.blit(texture, self.piece.texture_rect)
