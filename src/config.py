import pygame

APP_BG = (49, 46, 43)
SIDEBAR_BG = (62, 59, 56)
SIDEBAR_TEXT = (210, 210, 210)
SIDEBAR_MUTED = (150, 150, 150)
SIDEBAR_HIGHLIGHT = (80, 77, 74)
PLAYER_BAR_BG = (62, 59, 56)
TIMER_INACTIVE_BG = (72, 69, 66)
TIMER_INACTIVE_TEXT = (150, 150, 150)
TIMER_ACTIVE_BG = (30, 30, 30)
TIMER_ACTIVE_TEXT = (255, 255, 255)


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


class Theme:

    def __init__(self, name, light_bg, dark_bg, light_move, dark_move, trace_light, trace_dark):
        self.name = name
        self.bg = Bg(light_bg, dark_bg)
        self.moves = Moves(light_move, dark_move)
        self.trace = Trace(trace_light, trace_dark)


BOARD_THEMES = [
    Theme('Verde', (235, 236, 208), (119, 148, 85), (100, 120, 80), (80, 100, 60), (246, 246, 130), (246, 246, 105)),
    Theme('Marrom', (240, 217, 181), (181, 136, 99), (120, 100, 80), (100, 80, 60), (246, 246, 130), (246, 246, 105)),
    Theme('Azul', (222, 227, 230), (140, 162, 173), (100, 120, 140), (80, 100, 120), (246, 246, 130), (246, 246, 105)),
    Theme('Roxo', (230, 220, 240), (150, 130, 170), (120, 100, 140), (100, 80, 120), (246, 246, 130), (246, 246, 105)),
]


class Config:

    def __init__(self, theme_idx=0):
        self.themes = BOARD_THEMES
        self.font = pygame.font.Font(None, 22)
        self.sidebar_font = pygame.font.Font(None, 24)
        self.sidebar_title_font = pygame.font.Font(None, 28)
        self.player_font = pygame.font.Font(None, 26)
        self.timer_font = pygame.font.Font(None, 32)
        self.timer_font_active = pygame.font.Font(None, 34)
        self.idx = theme_idx
        self.theme = self.themes[self.idx]
        self.move_sound = pygame.mixer.Sound('assets/sounds/move.wav')
        self.capture_sound = pygame.mixer.Sound('assets/sounds/capture.wav')

    def set_theme(self, idx):
        self.idx = idx % len(self.themes)
        self.theme = self.themes[self.idx]

    def change_theme(self):
        self.set_theme(self.idx + 1)
