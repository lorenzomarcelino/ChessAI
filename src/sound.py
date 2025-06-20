try:
    import pygame
except ImportError:  # pragma: no cover - pygame optional for tests
    pygame = None

class Sound:

    def __init__(self, path):
        self.path = path
        if pygame:
            self.sound = pygame.mixer.Sound(path)
        else:
            self.sound = None

    def play(self):
        if pygame and self.sound:
            pygame.mixer.Sound.play(self.sound)
