"""Per person per day free block computation.

The workday is a fixed window (default 09:00 to 17:00). Meetings carve busy
intervals out of it. What is left are free blocks. The longest free block is the
best uninterrupted stretch a person could have used for focused work that day.

A day of six scattered half hour meetings leaves many short gaps and no long
one. A day with a single block leaves one long stretch. This module makes that
difference a number.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

from meetingtax.events import Occurrence


@dataclass(frozen=True)
class Workday:
    """The window each day within which focus time is measured."""

    start_hour: int = 9
    start_minute: int = 0
    end_hour: int = 17
    end_minute: int = 0

    def window(self, day: _dt.date) -> tuple[_dt.datetime, _dt.datetime]:
        start = _dt.datetime(
            day.year, day.month, day.day, self.start_hour, self.start_minute
        )
        end = _dt.datetime(day.year, day.month, day.day, self.end_hour, self.end_minute)
        return start, end

