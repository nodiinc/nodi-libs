#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schedule Example 2: DeltaSchedule usage."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from datetime import datetime

from nodi_libs.schedule import DeltaSchedule


def main():
    base = datetime(2025, 3, 15, 14, 30, 0)

    # Every 30 minutes
    print("=== Every 30 minutes ===")
    delta = DeltaSchedule('0-0-0 0:30:0', base_time=base)
    for dt in delta.get_next(5):
        print(f"  {dt}")

    # Every 1 day 12 hours
    print("\n=== Every 1 day 12 hours ===")
    delta = DeltaSchedule('0-0-1 12:0:0', base_time=base)
    for dt in delta.get_next(5):
        print(f"  {dt}")

    # Every 1 year
    print("\n=== Every 1 year ===")
    delta = DeltaSchedule('1-0-0 0:0:0', base_time=base)
    for dt in delta.get_next(5):
        print(f"  {dt}")

    # With microseconds (500ms interval)
    print("\n=== Every 500ms (microsecond) ===")
    delta = DeltaSchedule('0-0-0 0:0:0.500000', base_time=base)
    for dt in delta.get_next(5):
        print(f"  {dt}")

    # get_prev: previous times
    print("\n=== Previous 5 times (every 1 hour) ===")
    delta = DeltaSchedule('0-0-0 1:0:0', base_time=base)
    for dt in delta.get_prev(5):
        print(f"  {dt}")

    # Reset base time
    print("\n=== Reset base time ===")
    delta = DeltaSchedule('0-0-0 0:10:0', base_time=base)
    print(f"  base: {delta.base_time}")
    delta.get_next(3)
    print(f"  after get_next(3): {delta.base_time}")
    delta.set_base(base)
    print(f"  after set_base:    {delta.base_time}")


if __name__ == '__main__':
    main()
