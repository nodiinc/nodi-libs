#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FSM Example 1: Internal definition (FSM instance inside class)."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import time
from enum import Enum, auto

from nodi_libs.fsm import FiniteStateMachine


# 1. Define enum states
class SampleState(Enum):
    IDLE = auto()
    RUNNING = auto()
    ERROR = auto()
    STOPPED = auto()


# 2. Define machine class
class SampleMachine:

    # 3. Define all things in __init__
    def __init__(self):

        # 4. Create FSM instance in machine class
        self.fsm = FiniteStateMachine()
        self.count = 0

        # 5. Limit from/to transition states (optional)
        self.fsm.limit_transitions({
            SampleState.IDLE: [SampleState.RUNNING,
                               SampleState.STOPPED,
                               SampleState.ERROR],
            SampleState.RUNNING: [SampleState.IDLE],
            SampleState.ERROR: [SampleState.RUNNING],
        })

        # 6. Define action on transition with decorator (optional)
        @self.fsm.on_transition()
        def transition_handler(prev, next):
            print(f"Transitioned state: {prev} → {next}")

        # 7. Define action on error with decorator (optional)
        @self.fsm.on_error()
        def error_handler(error):
            print(f"Error handled: {error}")
            self.fsm.transition(SampleState.RUNNING)

        # 8. Define action on enter with decorator (optional)
        @self.fsm.on_enter(SampleState.RUNNING)
        def enter_run():
            print("RUNNING Enter Hook")

        # 9. Define action on exit with decorator (optional)
        @self.fsm.on_exit(SampleState.RUNNING)
        def exit_run():
            print("RUNNING Exit Hook")

        # 10. Define states with decorator
        @self.fsm.state(SampleState.IDLE)
        def idle_handler():
            print("[IDLE State] Waiting for events")
            time.sleep(0.05)

            # 11. Transition to another state
            if self.count in [4, 8]:
                self.fsm.transition(SampleState.ERROR)
            elif self.count >= 10:
                self.fsm.transition(SampleState.STOPPED)
            else:
                self.fsm.transition(SampleState.RUNNING)

        @self.fsm.state(SampleState.RUNNING)
        def running_handler():
            self.count += 1
            print(f"[RUNNING State] Processing count {self.count}")
            self.running_action()
            time.sleep(0.1)
            self.fsm.transition(SampleState.IDLE)

        @self.fsm.state(SampleState.ERROR)
        def error_handler():
            print("[ERROR State] Triggering failure")
            raise RuntimeError("Intentional failure for test")

        @self.fsm.state(SampleState.STOPPED)
        def stop_handler():
            print("[STOPPED State] Shutting down")

            # 12. Can call stop method in a state (optional)
            self.fsm.stop()

    def running_action(self):
        print("Running action")

    def run(self):

        # 13. Call start method
        self.fsm.start(SampleState.IDLE)
        external_count = 0

        # 14. Can check current state (optional)
        while self.fsm.current_state is not None:
            if external_count >= 5:
                break
            external_count += 1

            # 15. Can check running status (optional)
            print(f"Parallel external loop {external_count} "
                  f"(Is FSM running: {self.fsm.is_running})")
            time.sleep(1)


if __name__ == "__main__":
    # 16. Create machine instance
    system = SampleMachine()

    # 17. Call run method
    system.run()
