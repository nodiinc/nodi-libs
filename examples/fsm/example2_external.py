#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FSM Example 2: External definition (FSM instance outside class with bind)."""
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


# 2. First create FSM instance separated from machine class
fsm = FiniteStateMachine()


# 3. Then define machine class
class SampleMachine:

    def __init__(self):
        self.count = 0

        # 4. No need to define all things in __init__.
        #    But have to bind FSM instance to machine class.
        fsm.bind(self)

        fsm.limit_transitions({
            SampleState.IDLE: [SampleState.RUNNING,
                               SampleState.STOPPED,
                               SampleState.ERROR],
            SampleState.RUNNING: [SampleState.IDLE],
            SampleState.ERROR: [SampleState.RUNNING],
        })

    # 5. Define actions/states with decorator as class methods.
    #    And then the others are same as the usage example 1.
    @fsm.on_transition()
    def transition_handler(self, prev, next):
        print(f"Transitioned state: {prev} → {next}")

    @fsm.on_error()
    def error_handler(self, error):
        print(f"Error handled: {error}")
        fsm.transition(SampleState.RUNNING)

    @fsm.on_enter(SampleState.RUNNING)
    def enter_run(self):
        print("RUNNING Enter Hook")

    @fsm.on_exit(SampleState.RUNNING)
    def exit_run(self):
        print("RUNNING Exit Hook")

    @fsm.state(SampleState.IDLE)
    def idle_handler(self):
        print("[IDLE State] Waiting for events")
        time.sleep(0.05)
        if self.count in [4, 8]:
            fsm.transition(SampleState.ERROR)
        elif self.count >= 10:
            fsm.transition(SampleState.STOPPED)
        else:
            fsm.transition(SampleState.RUNNING)

    @fsm.state(SampleState.RUNNING)
    def running_handler(self):
        self.count += 1
        print(f"[RUNNING State] Processing count {self.count}")
        self.running_action()
        time.sleep(0.1)
        fsm.transition(SampleState.IDLE)

    @fsm.state(SampleState.ERROR)
    def error_handler(self):
        print("[ERROR State] Triggering failure")
        raise RuntimeError("Intentional failure for test")

    @fsm.state(SampleState.STOPPED)
    def stop_handler(self):
        print("[STOPPED State] Shutting down")
        fsm.stop()

    def running_action(self):
        print("Running action")

    def run(self):
        fsm.start(SampleState.IDLE)
        external_count = 0
        while fsm.current_state is not None:
            if external_count >= 5:
                break
            external_count += 1
            print(f"Parallel external loop {external_count} "
                  f"(Is FSM running: {fsm.is_running})")
            time.sleep(1)


if __name__ == "__main__":
    system = SampleMachine()
    system.run()
