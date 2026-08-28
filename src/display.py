import pygame

from config import s

DEFAULT_WINDOW_SIZE = (s(1040), s(860))


class Display:

    def __init__(self):
        self.fullscreen = False
        self.windowed_size = DEFAULT_WINDOW_SIZE
        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        pygame.display.set_caption('Chess')

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode(
                (info.current_w, info.current_h), pygame.FULLSCREEN
            )
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        return self.screen

    def on_resize(self, size):
        if self.fullscreen:
            return self.screen
        self.windowed_size = size
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        return self.screen
