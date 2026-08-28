import time


class TimeManager:
    def __init__(self, time_ms=None, remaining_ms=None, max_nodes=None):
        if time_ms is None and remaining_ms is not None:
            time_ms = self.alloc_move_time(remaining_ms)
        self.time_ms = time_ms
        self.max_nodes = max_nodes
        self.deadline = None
        self.nodes = 0

    @staticmethod
    def alloc_move_time(remaining_ms):
        allocated = int(remaining_ms * 0.06)
        return max(50, min(allocated, 30_000))

    def start(self):
        self.nodes = 0
        if self.time_ms is not None:
            self.deadline = time.perf_counter() + self.time_ms / 1000.0
        else:
            self.deadline = None

    def on_node(self):
        self.nodes += 1
        if self.max_nodes is not None and self.nodes >= self.max_nodes:
            return True
        if self.deadline is not None and (self.nodes & 63) == 0:
            if time.perf_counter() >= self.deadline:
                return True
        return False
