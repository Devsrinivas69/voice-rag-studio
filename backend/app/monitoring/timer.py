import time
from typing import Dict, Optional


class LatencyTimer:
    """Flexible context manager and manual timer for measuring stage latencies in milliseconds."""

    def __init__(
        self,
        stage_name: Optional[str] = "stage",
        breakdown_dict: Optional[Dict[str, Optional[float]]] = None,
    ):
        self.stage_name = stage_name or "stage"
        self.breakdown_dict = breakdown_dict
        self.elapsed_ms: float = 0.0
        self._start_time: float = 0.0

    def start(self):
        self._start_time = time.perf_counter()
        return self

    def stop(self) -> float:
        if self._start_time > 0:
            end_time = time.perf_counter()
            self.elapsed_ms = round((end_time - self._start_time) * 1000.0, 2)
            if self.breakdown_dict is not None and self.stage_name:
                self.breakdown_dict[self.stage_name] = self.elapsed_ms
        return self.elapsed_ms

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
