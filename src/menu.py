import pygame
import sys

from config import APP_BG, SIDEBAR_TEXT, SIDEBAR_MUTED, BOARD_THEMES
from settings import GameSettings, TIME_CONTROLS

TITLE_FONT_SIZE = 74
BODY_FONT_SIZE = 28
SMALL_FONT_SIZE = 24


def _fonts():
    return (
        pygame.font.Font(None, TITLE_FONT_SIZE),
        pygame.font.Font(None, BODY_FONT_SIZE),
        pygame.font.Font(None, SMALL_FONT_SIZE),
    )


def _draw_button(surface, rect, label, font, selected=False):
    bg = (90, 87, 84) if selected else (72, 69, 66)
    pygame.draw.rect(surface, bg, rect, border_radius=6)
    if selected:
        pygame.draw.rect(surface, (140, 180, 120), rect, width=2, border_radius=6)
    text = font.render(label, True, SIDEBAR_TEXT)
    surface.blit(text, text.get_rect(center=rect.center))


def draw_main_menu(screen):
    title_font, body_font, hint_font = _fonts()
    width, height = screen.get_size()
    screen.fill(APP_BG)
    screen.blit(title_font.render('Chess', True, SIDEBAR_TEXT), (width // 2 - 60, 140))
    screen.blit(body_font.render('Jogar', True, SIDEBAR_TEXT), (width // 2 - 40, 250))
    screen.blit(body_font.render('Sair', True, SIDEBAR_TEXT), (width // 2 - 30, 350))
    screen.blit(hint_font.render('F11: alternar tela cheia', True, SIDEBAR_MUTED), (width // 2 - 110, height - 50))


def draw_settings_menu(screen, settings):
    _, body_font, small_font = _fonts()
    width, height = screen.get_size()
    screen.fill(APP_BG)

    screen.blit(body_font.render('Configuracoes', True, SIDEBAR_TEXT), (width // 2 - 90, 40))
    screen.blit(small_font.render('Cor do tabuleiro', True, SIDEBAR_MUTED), (width // 2 - 80, 100))

    theme_buttons = []
    btn_w, btn_h = 110, 36
    start_x = width // 2 - (len(BOARD_THEMES) * (btn_w + 10)) // 2
    for i, theme in enumerate(BOARD_THEMES):
        rect = pygame.Rect(start_x + i * (btn_w + 10), 130, btn_w, btn_h)
        _draw_button(screen, rect, theme.name, small_font, selected=i == settings.theme_idx)
        theme_buttons.append((rect, i))

    screen.blit(small_font.render('Controle de tempo', True, SIDEBAR_MUTED), (width // 2 - 80, 190))

    time_buttons = []
    time_btn_w, time_btn_h = 160, 36
    cols = 2
    start_x = width // 2 - (cols * (time_btn_w + 12)) // 2
    for i, (label, _) in enumerate(TIME_CONTROLS):
        col = i % cols
        row = i // cols
        rect = pygame.Rect(start_x + col * (time_btn_w + 12), 220 + row * (time_btn_h + 10), time_btn_w, time_btn_h)
        _draw_button(screen, rect, label, small_font, selected=i == settings.time_idx)
        time_buttons.append((rect, i))

    start_rect = pygame.Rect(width // 2 - 90, height - 120, 180, 44)
    back_rect = pygame.Rect(width // 2 - 60, height - 60, 120, 36)
    _draw_button(screen, start_rect, 'Iniciar partida', body_font)
    _draw_button(screen, back_rect, 'Voltar', small_font)

    return theme_buttons, time_buttons, start_rect, back_rect


def main_menu(screen, display, start_game):
    settings = GameSettings()
    state = 'main'

    while True:
        if state == 'main':
            draw_main_menu(screen)
            theme_buttons = time_buttons = start_rect = back_rect = None
        else:
            theme_buttons, time_buttons, start_rect, back_rect = draw_settings_menu(screen, settings)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                screen = display.on_resize(event.size)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                screen = display.toggle_fullscreen()

            if event.type == pygame.MOUSEBUTTONDOWN:
                width, _ = screen.get_size()
                mouse_pos = event.pos

                if state == 'main':
                    if width // 2 - 50 <= mouse_pos[0] <= width // 2 + 50 and 250 <= mouse_pos[1] <= 300:
                        state = 'settings'
                    if width // 2 - 50 <= mouse_pos[0] <= width // 2 + 50 and 350 <= mouse_pos[1] <= 400:
                        pygame.quit()
                        sys.exit()
                else:
                    for rect, idx in theme_buttons:
                        if rect.collidepoint(mouse_pos):
                            settings.theme_idx = idx
                    for rect, idx in time_buttons:
                        if rect.collidepoint(mouse_pos):
                            settings.time_idx = idx
                    if start_rect.collidepoint(mouse_pos):
                        start_game(settings)
                        screen = display.screen
                    if back_rect.collidepoint(mouse_pos):
                        state = 'main'

        pygame.display.flip()
