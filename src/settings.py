import random

SIDE_OPTIONS = ('white', 'random', 'black')

TIME_CONTROLS = [
    ('1 min', 60),
    ('3 min', 180),
    ('5 min', 300),
    ('10 min', 600),
    ('15 min', 900),
    ('Sem tempo', 0),
]

TIME_GROUPS = [
    ('Blitz', 'bolt', (0, 1, 2)),
    ('Rapid', 'clock', (3, 4, 5)),
]


class GameSettings:

    def __init__(self, theme_idx=0, time_idx=5, side='white', opponent='human', ai_level=2):
        self.theme_idx = theme_idx
        self.time_idx = time_idx
        self.side = side
        self.opponent = opponent
        self.ai_level = ai_level

    @property
    def time_per_player(self):
        return TIME_CONTROLS[self.time_idx][1]

    @property
    def time_label(self):
        return TIME_CONTROLS[self.time_idx][0]

    @property
    def has_timer(self):
        return self.time_per_player > 0

    def resolve_bottom_color(self):
        if self.side == 'random':
            return random.choice(('white', 'black'))
        return self.side
