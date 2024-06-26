class Piece:
    def __init__(self, name, color, value):
        self.name = name
        self.color = color
        self.value = value
        self.moves = []
        self.moved = False
        self.set_texture()

    def set_texture(self, size=80):
        self.texture = f'assets/images/imgs-{size}px/{self.color}_{self.name}.png'

    def add_move(self, move):
        self.moves.append(move)

    def clear_moves(self):
        self.moves = []

class Pawn(Piece):
    def __init__(self, color):
        super().__init__('pawn', color, 1.0)
        self.dir = -1 if color == 'white' else 1
        self.en_passant = False

class Knight(Piece):
    def __init__(self, color):
        super().__init__('knight', color, 3.0)

class Bishop(Piece):
    def __init__(self, color):
        super().__init__('bishop', color, 3.0)

class Rook(Piece):
    def __init__(self, color):
        super().__init__('rook', color, 5.0)

class Queen(Piece):
    def __init__(self, color):
        super().__init__('queen', color, 9.0)

class King(Piece):
    def __init__(self, color):
        super().__init__('king', color, float('inf'))
        self.left_rook = None
        self.right_rook = None
