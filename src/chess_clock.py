import pygame

from settings import TIME_CONTROLS


class ChessClock:

    def __init__(self, seconds_per_player, enabled=True):
        self.enabled = enabled
        self.white_time = float(seconds_per_player)
        self.black_time = float(seconds_per_player)
        self.running = False
        self._last_tick = 0

    def start(self):
        if not self.enabled:
            return
        self.running = True
        self._last_tick = pygame.time.get_ticks()

    def tick(self, active_color):
        if not self.enabled or not self.running:
            return
        now = pygame.time.get_ticks()
        elapsed = (now - self._last_tick) / 1000.0
        self._last_tick = now
        if active_color == 'white':
            self.white_time = max(0.0, self.white_time - elapsed)
        else:
            self.black_time = max(0.0, self.black_time - elapsed)

    def stop(self):
        self.running = False

    def is_flagged(self, color):
        if not self.enabled:
            return False
        remaining = self.white_time if color == 'white' else self.black_time
        return remaining <= 0

    @staticmethod
    def format_time(seconds):
        total = max(0, int(seconds))
        minutes = total // 60
        secs = total % 60
        return f'{minutes}:{secs:02d}'

    def get_time(self, color):
        return self.white_time if color == 'white' else self.black_time
