# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import deque
from threading import Thread, RLock, current_thread, Event
from enum import Enum
from typing import Callable, Deque, Dict, Optional, List, Tuple
from time import time


class FiniteStateMachine:

    def __init__(self):
        # State
        self._state: Optional[Enum] = None
        self._handler: Optional[Callable] = None

        # Thread control
        self._thread: Optional[Thread] = None
        self._stop_event: Event = Event()
        self._stop_event.set()  # Initially stopped

        # Registry
        self._states: Dict[Enum, Callable] = {}
        self._allowed_transitions: Dict[Enum, List[Enum]] = {}

        # Hooks
        self._on_enter_hooks: Dict[Enum, Callable] = {}
        self._on_exit_hooks: Dict[Enum, Callable] = {}
        self._on_transition_callback: Optional[Callable[[Enum, Enum], None]] = None
        self._on_error_callback: Optional[Callable[[Exception], None]] = None

        # Transition queue (re-entry prevention)
        self._transition_queue: Deque[Tuple[Enum, bool]] = deque()
        self._is_transitioning: bool = False

        # Statistics
        self._transition_count: int = 0
        self._state_entry_time: Optional[float] = None

        # Thread safety
        self._lock = RLock()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Properties
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @property
    def is_running(self) -> bool:
        return not self._stop_event.is_set()

    @property
    def current_state(self) -> Optional[Enum]:
        return self._state

    @property
    def transition_count(self) -> int:
        return self._transition_count

    @property
    def time_in_current_state(self) -> Optional[float]:
        if self._state_entry_time is None:
            return None
        return time() - self._state_entry_time

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Core Loop
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _machine_loop(self):
        while not self._stop_event.is_set():
            handler = self._handler
            if handler is None:
                break

            try:
                handler()
            except Exception as exc:
                if self._on_error_callback:
                    try:
                        self._on_error_callback(exc)
                    except Exception:
                        break
                else:
                    self._stop_event.set()
                    break

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Lifecycle
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def start(self, initial_state: Enum):
        with self._lock:
            if not self._stop_event.is_set():
                return

            self._stop_event.clear()

            self.transition(initial_state)
            self._thread = Thread(target=self._machine_loop, daemon=True)
            self._thread.start()

    def stop(self, timeout: float = 5.0):
        with self._lock:
            if self._stop_event.is_set():
                return

            self._stop_event.set()
            thread_to_join = self._thread

            self._state = None
            self._handler = None
            self._transition_queue.clear()
            self._is_transitioning = False

        if thread_to_join and thread_to_join != current_thread():
            thread_to_join.join(timeout=timeout)

    def wait(self, timeout: Optional[float] = None) -> bool:
        if self._thread:
            self._thread.join(timeout=timeout)
            return not self._thread.is_alive()
        return True

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Transition
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def transition(self, next_state: Enum):
        with self._lock:
            self._transition_queue.append((next_state, False))
            self._process_transition_queue()

    def force_transition(self, next_state: Enum):
        with self._lock:
            self._transition_queue.append((next_state, True))
            self._process_transition_queue()

    def _process_transition_queue(self):
        if self._is_transitioning:
            return

        self._is_transitioning = True
        try:
            while self._transition_queue:
                next_state, is_forced = self._transition_queue.popleft()
                self._execute_transition(next_state, is_forced)
        finally:
            self._is_transitioning = False

    def _execute_transition(self, next_state: Enum, is_forced: bool):
        prev_state = self._state

        # Validation
        if next_state not in self._states:
            raise ValueError(f"No handler registered for state: {next_state}")
        if not is_forced and not self._can_transition(next_state):
            raise ValueError(f"Invalid transition: {prev_state} → {next_state}")

        # Exit hook
        if prev_state:
            exit_hook = self._on_exit_hooks.get(prev_state)
            if exit_hook:
                try:
                    exit_hook()
                except Exception:
                    pass

        # Update state
        self._state = next_state
        self._handler = self._states.get(next_state, self._missing_handler)
        self._state_entry_time = time()
        self._transition_count += 1

        # Transition callback
        if self._on_transition_callback:
            try:
                self._on_transition_callback(prev_state, next_state)
            except Exception:
                pass

        # Enter hook
        enter_hook = self._on_enter_hooks.get(next_state)
        if enter_hook:
            try:
                enter_hook()
            except Exception:
                pass

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Configuration
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def bind(self, instance: object) -> FiniteStateMachine:
        with self._lock:
            self._states = {k: v.__get__(instance)
                            for k, v in self._states.items()}
            self._on_enter_hooks = {k: v.__get__(instance)
                                    for k, v in self._on_enter_hooks.items()}
            self._on_exit_hooks = {k: v.__get__(instance)
                                   for k, v in self._on_exit_hooks.items()}
            if self._on_transition_callback:
                self._on_transition_callback = self._on_transition_callback.__get__(instance)
            if self._on_error_callback:
                self._on_error_callback = self._on_error_callback.__get__(instance)
            return self

    def limit_transitions(self, transitions: Dict[Enum, List[Enum]]):
        with self._lock:
            self._allowed_transitions = transitions

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Decorators
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def state(self, state: Enum):
        def decorator(func: Callable):
            self._states[state] = func
            return func
        return decorator

    def on_transition(self):
        def decorator(func: Callable[[Enum, Enum], None]):
            self._on_transition_callback = func
            return func
        return decorator

    def on_error(self):
        def decorator(func: Callable[[Exception], None]):
            self._on_error_callback = func
            return func
        return decorator

    def on_enter(self, state: Enum):
        def decorator(func: Callable):
            self._on_enter_hooks[state] = func
            return func
        return decorator

    def on_exit(self, state: Enum):
        def decorator(func: Callable):
            self._on_exit_hooks[state] = func
            return func
        return decorator

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Helper Methods
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _can_transition(self, next_state: Enum) -> bool:
        if self._state is None:
            return True
        allowed = self._allowed_transitions.get(self._state)
        return allowed is None or next_state in allowed

    def _missing_handler(self):
        raise ValueError(f"No handler defined for state: {self._state}")
