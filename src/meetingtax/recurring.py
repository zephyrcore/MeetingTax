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
    """A recurring VEVENT reduced to the facts that decide if it is stale."""

    uid: str
    summary: str
    freq: str
    interval: int
    attendee_count: int
    duration_minutes: int
    instances: int
    expanded: bool

    @property
    def stale(self) -> bool:
        """A recurring series this tool expanded and that never varies.

        Because each series carries one attendee set and one duration in the
        source, an expanded series with more than one instance is by definition
        unchanging across its run. Series we could not expand are not judged.
        """
        return self.expanded and self.instances > 1


def analyse(events: list[VEvent]) -> list[RecurringSeries]:
    """Return one RecurringSeries per VEVENT that carries an RRULE."""
    series: list[RecurringSeries] = []
    for event in events:
        rule = event.rrule
