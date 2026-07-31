TIME_CONTROLS = [
    ('Bullet (1 min)', 60),
    ('Blitz (3 min)', 180),
    ('Rapid (10 min)', 600),
    ('Normal (10 min)', 600),
    ('Sem tempo', 0),
]


class GameSettings:

    def __init__(self, theme_idx=0, time_idx=4):
        self.theme_idx = theme_idx
        self.time_idx = time_idx

    @property
    def time_per_player(self):
        return TIME_CONTROLS[self.time_idx][1]

    @property
    def time_label(self):
        return TIME_CONTROLS[self.time_idx][0]

    @property
    def has_timer(self):
        return self.time_per_player > 0
