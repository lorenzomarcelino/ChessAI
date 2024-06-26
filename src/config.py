import pygame

class Theme:

    def __init__(self, light_bg, dark_bg, light_move, dark_move, trace_light, trace_dark):
        self.bg = Bg(light_bg, dark_bg)
        self.moves = Moves(light_move, dark_move)
        self.trace = Trace(trace_light, trace_dark)

class Bg:

    def __init__(self, light, dark):
        self.light = light
        self.dark = dark

class Moves:

    def __init__(self, light, dark):
        self.light = light
        self.dark = dark

class Trace:

    def __init__(self, light, dark):
        self.light = light
        self.dark = dark

class Config:

    def __init__(self):
        self.themes = []
        self.font = pygame.font.Font(None, 30)
        self._add_themes()
        self.idx = 0
        self.theme = self.themes[self.idx]
        self.move_sound = pygame.mixer.Sound('assets/sounds/move.wav')
        self.capture_sound = pygame.mixer.Sound('assets/sounds/capture.wav')

    def _add_themes(self):
        green = Theme((234, 235, 200), (119, 154, 88), (244, 247, 116), (172, 195, 51), (250, 250, 210), (222, 226, 176))
        brown = Theme((240, 217, 181), (181, 136, 99), (255, 204, 153), (209, 139, 71), (230, 220, 187), (199, 185, 146))
        self.themes = [green, brown]

    def change_theme(self):
        self.idx = (self.idx + 1) % len(self.themes)
        self.theme = self.themes[self.idx]
