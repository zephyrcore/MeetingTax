"""Recurring series analysis.

A recurring meeting is stale when it repeats without its shape ever changing:
the same attendee set and the same duration on every instance. A weekly meeting
that has run unchanged for months is the kind of standing invite worth
questioning, because nobody has adjusted it to what the team now needs.
"""

from __future__ import annotations

from dataclasses import dataclass

from meetingtax.ics import VEvent


@dataclass
class RecurringSeries:
