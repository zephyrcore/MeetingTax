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

    @property
    def total_minutes(self) -> int:
        start = self.start_hour * 60 + self.start_minute
        end = self.end_hour * 60 + self.end_minute
        return max(0, end - start)


@dataclass
class DayFocus:
    """Focus analysis for one person on one day."""

    attendee: str
    day: _dt.date
    meeting_count: int
    busy_minutes: int
    longest_free_minutes: int
    free_blocks: list[tuple[_dt.datetime, _dt.datetime]] = field(default_factory=list)

    @property
    def longest_free_block(self) -> tuple[_dt.datetime, _dt.datetime] | None:
        if not self.free_blocks:
            return None
        return max(self.free_blocks, key=lambda b: b[1] - b[0])


def _merge_intervals(
    intervals: list[tuple[_dt.datetime, _dt.datetime]],
) -> list[tuple[_dt.datetime, _dt.datetime]]:
    """Merge overlapping or touching busy intervals into disjoint ones."""
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda iv: iv[0])
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _clip(
    interval: tuple[_dt.datetime, _dt.datetime],
    window: tuple[_dt.datetime, _dt.datetime],
) -> tuple[_dt.datetime, _dt.datetime] | None:
    """Clip a busy interval to the workday window, or drop it if outside."""
    start = max(interval[0], window[0])
    end = min(interval[1], window[1])
    if start >= end:
        return None
    return (start, end)


def compute_day(
    attendee: str,
    day: _dt.date,
    occurrences: list[Occurrence],
    workday: Workday,
) -> DayFocus:
    """Compute the free blocks and the longest one for a single day."""
    window = workday.window(day)
    busy_raw = [(o.start, o.end) for o in occurrences]
    clipped = [c for c in (_clip(iv, window) for iv in busy_raw) if c is not None]
    busy = _merge_intervals(clipped)

    busy_minutes = sum(int((e - s).total_seconds() // 60) for s, e in busy)

    free_blocks: list[tuple[_dt.datetime, _dt.datetime]] = []
    cursor = window[0]
    for start, end in busy:
        if start > cursor:
            free_blocks.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < window[1]:
        free_blocks.append((cursor, window[1]))

    longest = 0
    for start, end in free_blocks:
        minutes = int((end - start).total_seconds() // 60)
        longest = max(longest, minutes)

    return DayFocus(
        attendee=attendee,
        day=day,
        meeting_count=len(occurrences),
        busy_minutes=busy_minutes,
        longest_free_minutes=longest,
        free_blocks=free_blocks,
    )


def compute_all(
    occurrences: list[Occurrence],
    workday: Workday,
) -> list[DayFocus]:
    """Compute focus for every person on every day that has a meeting."""
    grouped: dict[tuple[str, _dt.date], list[Occurrence]] = {}
    for occ in occurrences:
        grouped.setdefault((occ.attendee, occ.day), []).append(occ)

    days: list[DayFocus] = []
    for (attendee, day), occ_list in grouped.items():
        days.append(compute_day(attendee, day, occ_list, workday))
    days.sort(key=lambda d: (d.attendee, d.day))
    return days


@dataclass
class PersonFocus:
    """A person's focus summary across all their meeting days."""

    attendee: str
    days: list[DayFocus]
    threshold_minutes: int

    @property
    def best_longest_free_minutes(self) -> int:
        return max((d.longest_free_minutes for d in self.days), default=0)

    @property
    def fragmented_days(self) -> int:
        """Days whose longest free block is below the declared threshold."""
        return sum(
            1 for d in self.days if d.longest_free_minutes < self.threshold_minutes
        )


def summarise_people(
    days: list[DayFocus], threshold_minutes: int
) -> list[PersonFocus]:
    """Group per day focus into a per person summary."""
    by_person: dict[str, list[DayFocus]] = {}
    for day in days:
        by_person.setdefault(day.attendee, []).append(day)
    people = [
        PersonFocus(
            attendee=name,
            days=sorted(day_list, key=lambda d: d.day),
            threshold_minutes=threshold_minutes,
        )
        for name, day_list in by_person.items()
    ]
    people.sort(key=lambda p: p.attendee)
    return people

# draft note 947
