# -*- coding: utf-8 -*-
from __future__ import annotations

import time
import threading
from typing import Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Periodic Timer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PeriodicTimer:

    def __init__(self, interval: float):
        self.interval = interval
        self._base_time: float = 0.0

    def wait(self, stop_event: Optional[threading.Event] = None) -> bool:
        curr_time = time.monotonic()

        # Init base time on first call
        if self._base_time == 0.0:
            self._base_time = curr_time

        # Calculate next aligned time
        elapsed = curr_time - self._base_time
        cycles = int(elapsed / self.interval) + 1
        next_time = self._base_time + cycles * self.interval

        # Wait
        wait_time = next_time - time.monotonic()
        if wait_time > 0:
            if stop_event:
                return stop_event.wait(timeout=wait_time)
            time.sleep(wait_time)
        return False

    def reset(self) -> None:
        self._base_time = 0.0
