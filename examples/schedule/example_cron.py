#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schedule Example 1: CronSchedule usage."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from datetime import datetime

from nodi_libs.schedule import CronSchedule


def main():
    base = datetime(2025, 3, 15, 14, 30, 0)

    # Every month, 1st day, 00:00:00
    print("=== Every month 1st, midnight ===")
    cron = CronSchedule('* 1 * 0 0 0', base_time=base)
    for dt in cron.get_next(5):
        print(f"  {dt}")

    # Every 5 minutes
    print("\n=== Every 5 minutes ===")
    cron = CronSchedule('* * * * */5 0', base_time=base)
    for dt in cron.get_next(5):
        print(f"  {dt}")

    # Every 10 seconds
    print("\n=== Every 10 seconds ===")
    cron = CronSchedule('* * * * * */10', base_time=base)
    for dt in cron.get_next(5):
        print(f"  {dt}")

    # N symbol: fix hour to current base_time hour (14)
    print(f"\n=== N symbol (base hour={base.hour}) ===")
    cron = CronSchedule('* * * N 0 0', base_time=base)
    for dt in cron.get_next(5):
        print(f"  {dt}")

    # Weekday: every Monday (1) at 09:00
    print("\n=== Every Monday 09:00 ===")
    cron = CronSchedule('* * 1 9 0 0', base_time=base)
    for dt in cron.get_next(5):
        print(f"  {dt}")

    # Return as float (unix timestamp)
    print("\n=== Return as float ===")
    cron = CronSchedule('* * * * */5 0', base_time=base, return_type=float)
    for ts in cron.get_next(3):
        print(f"  {ts}")

    # get_prev: previous schedules
    print("\n=== Previous 5 schedules (every hour) ===")
    cron = CronSchedule('* * * * 0 0', base_time=base)
    for dt in cron.get_prev(5):
        print(f"  {dt}")


if __name__ == '__main__':
    main()
