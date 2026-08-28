import sys
import ctypes
import pygame

APP_BG = (32, 30, 28)
SIDEBAR_BG = (48, 46, 43)
SIDEBAR_TEXT = (255, 255, 255)
SIDEBAR_MUTED = (181, 178, 174)
SIDEBAR_HIGHLIGHT = (72, 69, 66)
PLAYER_BAR_BG = (48, 46, 43)
TIMER_INACTIVE_BG = (57, 54, 51)
TIMER_INACTIVE_TEXT = (181, 178, 174)
TIMER_ACTIVE_BG = (30, 30, 30)
TIMER_ACTIVE_TEXT = (255, 255, 255)
BUTTON_BG = (48, 46, 43)
BUTTON_BG_HOVER = (62, 59, 56)
BUTTON_BG_SELECTED = (57, 54, 51)
BUTTON_BORDER = (129, 182, 76)
BUTTON_BORDER_HOVER = (90, 87, 84)
PLAY_GREEN = (129, 182, 76)
PLAY_GREEN_HOVER = (149, 196, 98)
PLAY_GREEN_SHADOW = (92, 133, 52)
TEXT_WHITE = (255, 255, 255)
SIDE_WHITE_BG = (232, 232, 230)
SIDE_BLACK_BG = (57, 54, 51)

_FONT_NAMES = 'segoeui,Segoe UI,calibri,Calibri,arial,Arial,dejavusans,sans'


def _dpi_scale():
    if sys.platform != 'win32':
        return 1.0
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return max(1.0, ctypes.windll.user32.GetDpiForSystem() / 96.0)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
        return 1.0


DPI_SCALE = _dpi_scale()


def s(value):
    return max(1, int(round(value * DPI_SCALE)))


def load_font(size, bold=False):
    px = s(size)
    try:
        font = pygame.font.SysFont(_FONT_NAMES, px, bold=bold)
        if font is not None:
            return font
    except Exception:
        pass
    return pygame.font.Font(None, px)


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
        self.font = load_font(16, bold=True)
        self.sidebar_font = load_font(18, bold=True)
        self.sidebar_title_font = load_font(22, bold=True)
        self.player_font = load_font(20, bold=True)
        self.timer_font = load_font(22, bold=True)
        self.timer_font_active = load_font(24, bold=True)
        self.idx = theme_idx
        self.theme = self.themes[self.idx]
        self.move_sound = pygame.mixer.Sound('assets/sounds/move.wav')
        self.capture_sound = pygame.mixer.Sound('assets/sounds/capture.wav')

    def set_theme(self, idx):
        self.idx = idx % len(self.themes)
        self.theme = self.themes[self.idx]

    def change_theme(self):
        self.set_theme(self.idx + 1)
