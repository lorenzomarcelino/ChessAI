import pygame

class Dragger:

    def __init__(self):
        self.piece = None
        self.dragging = False
        self.mouseX = 0
        self.mouseY = 0
        self.initial_row = 0
        self.initial_col = 0
        self.cell_size = 0

    def update_mouse(self, pos, cell_size, border_width, border_height):
        self.mouseX = pos[0] - border_width
        self.mouseY = pos[1] - border_height

    def save_initial(self, pos, cell_size, border_width, border_height):
        self.cell_size = cell_size
        self.initial_row = (pos[1] - border_height) // cell_size
        self.initial_col = (pos[0] - border_width) // cell_size

    def drag_piece(self, piece):
        self.piece = piece
        self.dragging = True

    def undrag_piece(self):
        self.piece = None
        self.dragging = False

    def update_blit(self, surface, cell_size, border_width, border_height):
        self.piece.set_texture(size=128)  # Certifique-se de usar imagens de 128px durante o arrasto
        texture = pygame.image.load(self.piece.texture)
        img_center = (self.mouseX + border_width, self.mouseY + border_height)
        self.piece.texture_rect = texture.get_rect(center=img_center)
        surface.blit(texture, self.piece.texture_rect)
