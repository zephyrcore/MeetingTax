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
        if rule is None:
            continue
        if event.dtstart is None or event.dtend is None:
            continue
        duration = max(
            0, int((event.dtend.value - event.dtstart.value).total_seconds() // 60)
        )
        organizer_set = {event.organizer} if event.organizer else set()
        attendee_count = len(set(event.attendees) | organizer_set)
        instances = _instance_count(rule)
        series.append(
            RecurringSeries(
                uid=event.uid,
                summary=event.summary,
                freq=rule.freq or "UNKNOWN",
                interval=max(1, rule.interval),
                attendee_count=attendee_count,
                duration_minutes=duration,
                instances=instances,
                expanded=rule.expandable,
            )
        )
    series.sort(key=lambda s: (s.uid, s.summary))
    return series


def _instance_count(rule) -> int:
    """A best effort instance count, only meaningful for expandable rules."""
    if not rule.expandable:
        return 1
    if rule.count is not None:
        return rule.count
    # Unbounded or UNTIL-bounded series report a count of at least two so the
    # staleness check treats them as repeating. The exact horizon is not the
    # point; the point is that the shape never changes.
    return 2


def stale_series(events: list[VEvent]) -> list[RecurringSeries]:
    """Just the series judged stale, for callers that want the finding set."""
    return [s for s in analyse(events) if s.stale]
