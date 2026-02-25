# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from re import findall, match
from typing import List, Optional, Type, Union

from croniter import croniter
from dateutil.relativedelta import relativedelta


# Nodi Cron Expression Reference
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# nodi cron: 6 fields (largest → smallest time unit)
#   +-----+---------+------------------+---------------+
#   | no. | field   | range            | symbol        |
#   +-----+---------+------------------+---------------+
#   | 1   | month   | 1~12 | JAN~DEC  | * - , / N     |
#   | 2   | date    | 1~31             | * - , / N L   |
#   | 3   | weekday | 0~6  | SUN~SAT  | * - , / N #   |
#   | 4   | hour    | 0~23             | * - , / N     |
#   | 5   | minute  | 0~59             | * - , / N     |
#   | 6   | second  | 0~59             | * - , / N     |
#   +-----+---------+------------------+---------------+
#
# croniter cron: 6 fields (for internal mapping reference)
#   +-----+---------+------------------+---------------+
#   | no. | field   | range            | symbol        |
#   +-----+---------+------------------+---------------+
#   | 1   | minute  | 0~59             | * - , /       |
#   | 2   | hour    | 0~23             | * - , /       |
#   | 3   | date    | 1~31             | * - , / L     |
#   | 4   | month   | 1~12 | JAN~DEC  | * - , /       |
#   | 5   | weekday | 0~6  | SUN~SAT  | * - , / #     |
#   | 6   | second  | 0~59             | * - , /       |
#   +-----+---------+------------------+---------------+
#
# Symbols
#   +--------+----------------+-------------+---------------------------+
#   | symbol | description    | example     | note                      |
#   +--------+----------------+-------------+---------------------------+
#   | *      | all            |             |                           |
#   | -      | range          | MON-WED     |                           |
#   | ,      | list           | MON,TUE,WED |                           |
#   | /      | start/unit     | */5         | every 5 units             |
#   | N      | now            |             | replaced by base_time     |
#   | ?      | none           |             |                           |
#   | L      | last           |             | last day of month         |
#   | W      | coming weekday |             | nearest MON~FRI           |
#   | #      | day of week    | 3#2         | 3rd weekday of 2nd week   |
#   +--------+----------------+-------------+---------------------------+
#
# Delta Expression Reference
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Format: Y-M-D H:m:S  or  Y-M-D H:m:S.us
#   +-------+-------------+----------+
#   | field | description | example  |
#   +-------+-------------+----------+
#   | Y     | years       | 1-0-0    |
#   | M     | months      | 0-6-0    |
#   | D     | days        | 0-0-30   |
#   | H     | hours       | 0:12:0   |
#   | m     | minutes     | 0:0:30   |
#   | S     | seconds     | 0:0:5    |
#   | us    | microseconds| 0:0:0.500|
#   +-------+-------------+----------+
#
# Examples:
#   '1-0-0 0:0:0'       → 1 year interval
#   '0-0-0 0:30:0'      → 30 minute interval
#   '0-0-1 12:0:0'      → 1 day 12 hours interval
#   '0-0-0 0:0:0.500000'→ 500ms interval


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CronSchedule
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CronSchedule:

    _FIELD_COUNT = 6

    def __init__(self,
                 cron_expression: str = '* * * * * *',
                 base_time: Optional[datetime] = None,
                 return_type: Type = datetime):
        self._cron_expression = cron_expression
        self._return_type = return_type
        self._base_time: datetime = base_time or datetime.now()


    # Properties
    # ──────────────────────────────────────────────────────────────────────

    @property
    def base_time(self) -> datetime:
        return self._base_time


    # Public Methods
    # ──────────────────────────────────────────────────────────────────────

    def set_base(self, base_time: Optional[datetime] = None) -> None:
        self._base_time = base_time or datetime.now()

    def get_next(self, count: int = 1) -> List[Union[datetime, float]]:
        cron = self._build_croniter()
        results = []
        for _ in range(count):
            results.append(cron.get_next())
        self._base_time = cron.get_current(datetime)
        return results

    def get_prev(self, count: int = 1) -> List[Union[datetime, float]]:
        cron = self._build_croniter()
        results = []
        for _ in range(count):
            results.append(cron.get_prev())
        self._base_time = cron.get_current(datetime)
        return results


    # Private Methods
    # ──────────────────────────────────────────────────────────────────────

    def _build_croniter(self) -> croniter:
        fields = self._cron_expression.split()
        if len(fields) != self._FIELD_COUNT:
            raise ValueError(
                f"expected {self._FIELD_COUNT} fields "
                f"(month date weekday hour minute second), got {len(fields)}"
            )
        month, date, weekday, hour, minute, second = fields

        # Replace N symbol with base_time field values
        month = month.replace('N', str(self._base_time.month))
        date = date.replace('N', str(self._base_time.day))
        weekday = weekday.replace('N', str(self._base_time.weekday()))
        hour = hour.replace('N', str(self._base_time.hour))
        minute = minute.replace('N', str(self._base_time.minute))
        second = second.replace('N', str(self._base_time.second))

        # Convert nodi field order → croniter field order
        # nodi:     month date weekday hour minute second
        # croniter: minute hour date month weekday second
        croniter_expression = f"{minute} {hour} {date} {month} {weekday} {second}"

        return croniter(expr_format=croniter_expression,
                        start_time=self._base_time,
                        ret_type=self._return_type)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DeltaSchedule
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DeltaSchedule:

    _PATTERN_WITH_MICROSECOND = r'^\d+-\d+-\d+ \d+:\d+:\d+\.\d+$'
    _PATTERN_WITHOUT_MICROSECOND = r'^\d+-\d+-\d+ \d+:\d+:\d+$'

    def __init__(self,
                 delta_expression: str = '0-0-0 0:0:0',
                 base_time: Optional[datetime] = None):
        self._base_time: datetime = base_time or datetime.now()
        self._delta = self._parse_delta(delta_expression)


    # Properties
    # ──────────────────────────────────────────────────────────────────────

    @property
    def base_time(self) -> datetime:
        return self._base_time


    # Public Methods
    # ──────────────────────────────────────────────────────────────────────

    def set_base(self, base_time: Optional[datetime] = None) -> None:
        self._base_time = base_time or datetime.now()

    def get_next(self, count: int = 1) -> List[datetime]:
        results = []
        current = self._base_time
        for _ in range(count):
            current = current + self._delta
            results.append(current)
        self._base_time = current
        return results

    def get_prev(self, count: int = 1) -> List[datetime]:
        results = []
        current = self._base_time
        for _ in range(count):
            current = current - self._delta
            results.append(current)
        self._base_time = current
        return results


    # Private Methods
    # ──────────────────────────────────────────────────────────────────────

    def _parse_delta(self, delta_expression: str) -> relativedelta:
        has_microsecond = bool(match(self._PATTERN_WITH_MICROSECOND, delta_expression))
        has_no_microsecond = bool(match(self._PATTERN_WITHOUT_MICROSECOND, delta_expression))

        if not has_microsecond and not has_no_microsecond:
            raise ValueError(
                f"invalid delta format: '{delta_expression}', "
                f"expected 'Y-M-D H:m:S' or 'Y-M-D H:m:S.us'"
            )

        numbers = [int(n) for n in findall(r'\d+', delta_expression)]
        years, months, days = numbers[0], numbers[1], numbers[2]
        hours, minutes, seconds = numbers[3], numbers[4], numbers[5]
        microseconds = numbers[6] if has_microsecond else 0

        return relativedelta(years=years,
                             months=months,
                             days=days,
                             hours=hours,
                             minutes=minutes,
                             seconds=seconds,
                             microseconds=microseconds)
