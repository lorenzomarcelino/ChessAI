from pathlib import Path

import pygame
import sys

from config import (
    APP_BG, SIDEBAR_MUTED, BOARD_THEMES, TEXT_WHITE,
    BUTTON_BG, BUTTON_BG_HOVER, BUTTON_BG_SELECTED,
    BUTTON_BORDER, PLAY_GREEN, PLAY_GREEN_HOVER, PLAY_GREEN_SHADOW,
    SIDE_WHITE_BG, SIDE_BLACK_BG, load_font, s,
)
from settings import GameSettings, TIME_CONTROLS, TIME_GROUPS, SIDE_OPTIONS

OPPONENT_OPTIONS = (
    ('human', 'Humano'),
    ('ai', 'Própria'),
    ('ai_sf', 'Destilada'),
)
AI_LEVEL_OPTIONS = (
    ('Iniciante', 0),
    ('Fácil', 1),
    ('Médio', 2),
    ('Difícil', 3),
    ('Mestre', 4),
)

_ENGINE_INFO = (
    ('Humano', 'Outra pessoa neste computador. Sem inteligência artificial.'),
    (
        'Própria',
        'IA feita e treinada só por nós, com partidas da internet. '
        'Joga de forma mais simples. É a mais fraca das duas IAs.',
    ),
    (
        'Destilada',
        'IA nossa ensinada pelo Stockfish. Ele não joga: só ajuda a escolher '
        'os primeiros lances e a abertura. A busca é mais rápida e profunda. '
        'É a mais forte. Use esta contra um desafio maior.',
    ),
)


_KING_CACHE = {}


def _king_image(color, size):
    key = (color, size)
    if key not in _KING_CACHE:
        path = f'assets/images/imgs-80px/{color}_king.png'
        img = pygame.image.load(path).convert_alpha()
        _KING_CACHE[key] = pygame.transform.smoothscale(img, (size, size))
    return _KING_CACHE[key]


def _centered_rect(cx, cy, width, height):
    rect = pygame.Rect(0, 0, width, height)
    rect.center = (cx, cy)
    return rect


def draw_button(surface, rect, label, font, selected=False, hovered=False):
    if selected:
        bg = BUTTON_BG_SELECTED
    elif hovered:
        bg = BUTTON_BG_HOVER
    else:
        bg = BUTTON_BG

    radius = s(6)
    pygame.draw.rect(surface, bg, rect, border_radius=radius)
    if selected:
        pygame.draw.rect(surface, BUTTON_BORDER, rect, width=s(3), border_radius=radius)

    text = font.render(label, True, TEXT_WHITE)
    surface.blit(text, text.get_rect(center=rect.center))


def draw_play_button(surface, rect, label, font, hovered=False):
    radius = s(8)
    pygame.draw.rect(surface, PLAY_GREEN_SHADOW, rect, border_radius=radius)
    face = pygame.Rect(rect.x, rect.y, rect.w, max(s(8), rect.h - s(5)))
    color = PLAY_GREEN_HOVER if hovered else PLAY_GREEN
    pygame.draw.rect(surface, color, face, border_radius=radius)
    text = font.render(label, True, TEXT_WHITE)
    surface.blit(text, text.get_rect(center=(rect.centerx, face.centery)))


def distilled_model_ready():
    return (Path(__file__).resolve().parents[1] / 'models' / 'value_sf.pt').is_file()


def _wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ''
    for word in words:
        trial = word if not current else f'{current} {word}'
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_info_button(surface, rect, hovered=False):
    color = PLAY_GREEN if hovered else SIDEBAR_MUTED
    pygame.draw.circle(surface, color, rect.center, rect.w // 2, width=s(2))
    font = load_font(14, bold=True)
    label = font.render('i', True, color)
    surface.blit(label, label.get_rect(center=(rect.centerx, rect.centery - s(1))))


def draw_engine_info_overlay(screen, mouse_pos):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    title_font = load_font(26, bold=True)
    name_font = load_font(18, bold=True)
    body_font = load_font(16)
    close_font = load_font(18, bold=True)
    width, height = screen.get_size()
    panel_w = min(s(520), width - s(40))
    pad = s(22)
    text_w = panel_w - pad * 2

    blocks = []
    content_h = 0
    for name, blurb in _ENGINE_INFO:
        lines = _wrap_text(blurb, body_font, text_w)
        extra = '  ·  recomendada' if name == 'Destilada' else ''
        name_h = name_font.size(name + extra)[1]
        line_h = body_font.get_height()
        block_h = name_h + s(6) + len(lines) * (line_h + s(2))
        blocks.append((name, extra, lines, block_h))
        content_h += block_h + s(16)

    note = None
    if not distilled_model_ready():
        note = (
            'A Destilada ainda não tem o arquivo treinado (models/value_sf.pt). '
            'Até treinar, ela usa só a busca clássica.'
        )
        note_lines = _wrap_text(note, body_font, text_w)
        note_h = len(note_lines) * (body_font.get_height() + s(2)) + s(8)
        content_h += note_h
    else:
        note_lines = []
        note_h = 0

    title_h = title_font.get_height()
    close_h = s(42)
    panel_h = pad + title_h + s(18) + content_h + close_h + pad
    panel_h = min(panel_h, height - s(40))
    panel = pygame.Rect(0, 0, panel_w, panel_h)
    panel.center = (width // 2, height // 2)

    pygame.draw.rect(screen, (42, 40, 38), panel, border_radius=s(12))
    pygame.draw.rect(screen, BUTTON_BORDER, panel, width=s(2), border_radius=s(12))

    title = title_font.render('Quem joga contra você', True, TEXT_WHITE)
    screen.blit(title, (panel.x + pad, panel.y + pad))
    y = panel.y + pad + title_h + s(16)

    for name, extra, lines, _block_h in blocks:
        name_surf = name_font.render(name, True, TEXT_WHITE)
        screen.blit(name_surf, (panel.x + pad, y))
        if extra:
            tag = name_font.render('recomendada', True, PLAY_GREEN)
            screen.blit(tag, (panel.x + pad + name_surf.get_width() + s(10), y))
        y += name_surf.get_height() + s(6)
        for line in lines:
            line_surf = body_font.render(line, True, SIDEBAR_MUTED)
            screen.blit(line_surf, (panel.x + pad, y))
            y += line_surf.get_height() + s(2)
        y += s(12)

    if note_lines:
        for line in note_lines:
            line_surf = body_font.render(line, True, (220, 170, 90))
            screen.blit(line_surf, (panel.x + pad, y))
            y += line_surf.get_height() + s(2)
        y += s(8)

    close_rect = pygame.Rect(panel.centerx - s(70), panel.bottom - pad - close_h, s(140), close_h)
    draw_button(screen, close_rect, 'Fechar', close_font, hovered=close_rect.collidepoint(mouse_pos))
    return panel, close_rect


def _draw_bolt(surface, x, y, size):
    w = h = size
    points = [
        (x + w * 0.58, y),
        (x + w * 0.18, y + h * 0.52),
        (x + w * 0.48, y + h * 0.52),
        (x + w * 0.38, y + h),
        (x + w * 0.82, y + h * 0.42),
        (x + w * 0.52, y + h * 0.42),
    ]
    pygame.draw.polygon(surface, (255, 204, 0), points)


def _draw_clock_icon(surface, x, y, size):
    color = (129, 182, 76)
    cx = x + size // 2
    cy = y + size // 2
    r = max(3, size // 2 - 1)
    width = max(2, s(2))
    pygame.draw.circle(surface, color, (cx, cy), r, width)
    pygame.draw.line(surface, color, (cx, cy), (cx, cy - r + s(4)), width)
    pygame.draw.line(surface, color, (cx, cy), (cx + r // 2, cy + s(2)), width)


def _draw_section_title(surface, text, font, x, y, icon=None):
    icon_size = s(18)
    label = font.render(text, True, TEXT_WHITE)
    height = max(icon_size, label.get_height())
    if icon == 'bolt':
        _draw_bolt(surface, x, y + (height - icon_size) // 2, icon_size)
        tx = x + icon_size + s(8)
    elif icon == 'clock':
        _draw_clock_icon(surface, x, y + (height - icon_size) // 2, icon_size)
        tx = x + icon_size + s(8)
    else:
        tx = x
    surface.blit(label, (tx, y + (height - label.get_height()) // 2))
    return height


def _draw_side_button(surface, rect, side, selected, hovered):
    radius = s(10)
    if side == 'white':
        pygame.draw.rect(surface, SIDE_WHITE_BG, rect, border_radius=radius)
        king = _king_image('black', int(rect.h * 0.72))
        surface.blit(king, king.get_rect(center=rect.center))
    elif side == 'black':
        pygame.draw.rect(surface, SIDE_BLACK_BG, rect, border_radius=radius)
        king = _king_image('white', int(rect.h * 0.72))
        surface.blit(king, king.get_rect(center=rect.center))
    else:
        pygame.draw.rect(surface, SIDE_WHITE_BG, rect, border_radius=radius)
        right = pygame.Rect(rect.centerx, rect.y, rect.width - rect.width // 2, rect.height)
        previous_clip = surface.get_clip()
        surface.set_clip(right)
        pygame.draw.rect(surface, SIDE_BLACK_BG, rect, border_radius=radius)
        surface.set_clip(previous_clip)
        font = load_font(32, bold=True)
        q_dark = font.render('?', True, SIDE_BLACK_BG)
        q_light = font.render('?', True, SIDE_WHITE_BG)
        q_rect = q_dark.get_rect(center=rect.center)
        left = pygame.Rect(rect.x, rect.y, rect.width // 2, rect.height)
        surface.set_clip(left)
        surface.blit(q_dark, q_rect)
        surface.set_clip(right)
        surface.blit(q_light, q_rect)
        surface.set_clip(previous_clip)

    if selected:
        pygame.draw.rect(surface, PLAY_GREEN, rect, width=s(4), border_radius=radius)
    elif hovered:
        pygame.draw.rect(surface, BUTTON_BORDER, rect, width=s(2), border_radius=radius)


def _draw_theme_preview(surface, rect, theme, selected, hovered, font):
    radius = s(8)
    bg = BUTTON_BG_HOVER if hovered or selected else BUTTON_BG
    pygame.draw.rect(surface, bg, rect, border_radius=radius)
    if selected:
        pygame.draw.rect(surface, PLAY_GREEN, rect, width=s(3), border_radius=radius)

    pad = s(8)
    label_h = s(24)
    board_w = rect.w - pad * 2
    board_h = rect.h - pad * 2 - label_h
    board_size = min(board_w, board_h)
    board = pygame.Rect(0, 0, board_size, board_size)
    board.midtop = (rect.centerx, rect.y + pad)

    cells = 4
    cell = board.w // cells
    for row in range(cells):
        for col in range(cells):
            color = theme.bg.light if (row + col) % 2 == 0 else theme.bg.dark
            pygame.draw.rect(
                surface, color,
                (board.x + col * cell, board.y + row * cell, cell, cell),
            )

    name = font.render(theme.name, True, TEXT_WHITE)
    surface.blit(name, name.get_rect(midtop=(rect.centerx, board.bottom + s(4))))


def draw_main_menu(screen, mouse_pos):
    title_font = load_font(64, bold=True)
    play_font = load_font(30, bold=True)
    body_font = load_font(22, bold=True)
    hint_font = load_font(18, bold=True)
    width, height = screen.get_size()
    cx = width // 2
    screen.fill(APP_BG)

    title = title_font.render('Chess', True, TEXT_WHITE)
    title_rect = title.get_rect(center=(cx, int(height * 0.26)))
    screen.blit(title, title_rect)

    btn_w, play_h, quit_h = s(320), s(62), s(52)
    gap = s(16)
    play_rect = _centered_rect(cx, title_rect.bottom + gap + play_h // 2 + s(12), btn_w, play_h)
    quit_rect = _centered_rect(cx, play_rect.bottom + gap + quit_h // 2, btn_w, quit_h)

    draw_play_button(screen, play_rect, 'Jogar', play_font, hovered=play_rect.collidepoint(mouse_pos))
    draw_button(screen, quit_rect, 'Sair', body_font, hovered=quit_rect.collidepoint(mouse_pos))

    hint = hint_font.render('F11: alternar tela cheia', True, SIDEBAR_MUTED)
    screen.blit(hint, hint.get_rect(center=(cx, height - s(40))))

    return play_rect, quit_rect


def draw_settings_menu(screen, settings, mouse_pos):
    title_font = load_font(34, bold=True)
    section_font = load_font(20, bold=True)
    time_font = load_font(20, bold=True)
    play_font = load_font(28, bold=True)
    back_font = load_font(20, bold=True)
    theme_font = load_font(16, bold=True)
    width, height = screen.get_size()
    cx = width // 2
    screen.fill(APP_BG)

    panel_w = s(460)
    left = cx - panel_w // 2
    y = s(16)
    gap = s(8)

    title = title_font.render('Nova partida', True, TEXT_WHITE)
    screen.blit(title, title.get_rect(center=(cx, y + title.get_height() // 2)))
    y = title.get_rect(center=(cx, y + title.get_height() // 2)).bottom + s(14)

    side_label = section_font.render('Você joga de', True, TEXT_WHITE)
    screen.blit(side_label, (left, y))
    y += side_label.get_height() + s(12)

    side_size = s(52)
    side_gap = s(12)
    row_w = 3 * side_size + 2 * side_gap
    side_x = cx - row_w // 2
    side_buttons = []
    for i, side in enumerate(SIDE_OPTIONS):
        rect = pygame.Rect(side_x + i * (side_size + side_gap), y, side_size, side_size)
        _draw_side_button(
            screen, rect, side,
            selected=settings.side == side,
            hovered=rect.collidepoint(mouse_pos),
        )
        side_buttons.append((rect, side))
    y += side_size + s(16)

    opp_label = section_font.render('Oponente', True, TEXT_WHITE)
    screen.blit(opp_label, (left, y))
    info_size = s(24)
    info_rect = pygame.Rect(
        left + opp_label.get_width() + s(8),
        y + max(0, (opp_label.get_height() - info_size) // 2),
        info_size,
        info_size,
    )
    _draw_info_button(screen, info_rect, hovered=info_rect.collidepoint(mouse_pos))
    y += opp_label.get_height() + s(10)

    opponent_buttons = []
    n_opp = len(OPPONENT_OPTIONS)
    opp_w = (panel_w - (n_opp - 1) * gap) // n_opp
    opp_h = s(40)
    for i, (value, label) in enumerate(OPPONENT_OPTIONS):
        rect = pygame.Rect(left + i * (opp_w + gap), y, opp_w, opp_h)
        draw_button(
            screen, rect, label, theme_font,
            selected=settings.opponent == value,
            hovered=rect.collidepoint(mouse_pos),
        )
        opponent_buttons.append((rect, value))
    y += opp_h + s(12)

    skill_buttons = []
    if settings.opponent in ('ai', 'ai_sf'):
        skill_label = section_font.render('Dificuldade', True, TEXT_WHITE)
        screen.blit(skill_label, (left, y))
        y += skill_label.get_height() + s(10)
        skill_w = (panel_w - 4 * gap) // 5
        skill_h = s(36)
        for i, (label, level) in enumerate(AI_LEVEL_OPTIONS):
            rect = pygame.Rect(left + i * (skill_w + gap), y, skill_w, skill_h)
            draw_button(
                screen, rect, label, theme_font,
                selected=settings.ai_level == level,
                hovered=rect.collidepoint(mouse_pos),
            )
            skill_buttons.append((rect, level))
        y += skill_h + s(16)
    y += s(4)

    theme_label = section_font.render('Cor do tabuleiro', True, TEXT_WHITE)
    screen.blit(theme_label, (left, y))
    y += theme_label.get_height() + s(12)

    theme_buttons = []
    theme_gap = s(10)
    theme_w = (panel_w - 3 * theme_gap) // 4
    theme_h = s(78)
    for i, theme in enumerate(BOARD_THEMES):
        rect = pygame.Rect(left + i * (theme_w + theme_gap), y, theme_w, theme_h)
        _draw_theme_preview(
            screen, rect, theme,
            selected=i == settings.theme_idx,
            hovered=rect.collidepoint(mouse_pos),
            font=theme_font,
        )
        theme_buttons.append((rect, i))
    y += theme_h + s(12)

    time_buttons = []
    cols = 3
    time_h = s(40)
    time_w = (panel_w - (cols - 1) * gap) // cols

    for group_name, icon, indexes in TIME_GROUPS:
        title_h = _draw_section_title(screen, group_name, section_font, left, y, icon=icon)
        y += title_h + s(10)
        for i, idx in enumerate(indexes):
            col = i % cols
            row = i // cols
            rect = pygame.Rect(
                left + col * (time_w + gap),
                y + row * (time_h + gap),
                time_w,
                time_h,
            )
            draw_button(
                screen, rect, TIME_CONTROLS[idx][0], time_font,
                selected=idx == settings.time_idx,
                hovered=rect.collidepoint(mouse_pos),
            )
            time_buttons.append((rect, idx))
        rows = (len(indexes) + cols - 1) // cols
        y += rows * (time_h + gap) + s(8)

    y += s(6)
    start_rect = pygame.Rect(left, y, panel_w, s(58))
    draw_play_button(
        screen, start_rect, 'Jogar', play_font,
        hovered=start_rect.collidepoint(mouse_pos),
    )
    back_rect = pygame.Rect(left + panel_w // 2 - s(80), start_rect.bottom + s(12), s(160), s(42))
    draw_button(screen, back_rect, 'Voltar', back_font, hovered=back_rect.collidepoint(mouse_pos))

    return theme_buttons, time_buttons, side_buttons, opponent_buttons, skill_buttons, start_rect, back_rect, info_rect


def main_menu(screen, display, start_game):
    settings = GameSettings()
    state = 'main'
    show_engine_info = False
    clock = pygame.time.Clock()

    while True:
        mouse_pos = pygame.mouse.get_pos()
        info_rect = None
        info_panel = close_rect = None
        if state == 'main':
            play_rect, quit_rect = draw_main_menu(screen, mouse_pos)
            theme_buttons = time_buttons = side_buttons = None
            opponent_buttons = skill_buttons = start_rect = back_rect = None
        else:
            play_rect = quit_rect = None
            (
                theme_buttons, time_buttons, side_buttons, opponent_buttons,
                skill_buttons, start_rect, back_rect, info_rect,
            ) = draw_settings_menu(screen, settings, mouse_pos)
            if show_engine_info:
                info_panel, close_rect = draw_engine_info_overlay(screen, mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                screen = display.on_resize(event.size)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    screen = display.toggle_fullscreen()
                elif event.key == pygame.K_ESCAPE and show_engine_info:
                    show_engine_info = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos

                if show_engine_info:
                    if close_rect is not None and close_rect.collidepoint(mouse_pos):
                        show_engine_info = False
                    elif info_panel is not None and not info_panel.collidepoint(mouse_pos):
                        show_engine_info = False
                    continue

                if state == 'main':
                    if play_rect.collidepoint(mouse_pos):
                        state = 'settings'
                    elif quit_rect.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()
                else:
                    if info_rect is not None and info_rect.collidepoint(mouse_pos):
                        show_engine_info = True
                        continue
                    for rect, idx in theme_buttons:
                        if rect.collidepoint(mouse_pos):
                            settings.theme_idx = idx
                    for rect, idx in time_buttons:
                        if rect.collidepoint(mouse_pos):
                            settings.time_idx = idx
                    for rect, side in side_buttons:
                        if rect.collidepoint(mouse_pos):
                            settings.side = side
                    for rect, opponent in opponent_buttons:
                        if rect.collidepoint(mouse_pos):
                            settings.opponent = opponent
                    for rect, level in skill_buttons:
                        if rect.collidepoint(mouse_pos):
                            settings.ai_level = level
                    if start_rect.collidepoint(mouse_pos):
                        start_game(settings)
                        screen = display.screen
                    elif back_rect.collidepoint(mouse_pos):
                        state = 'main'

        pygame.display.flip()
        clock.tick(60)
