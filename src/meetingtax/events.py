"""Event models and expansion of VEVENTs into concrete dated occurrences.

An occurrence is one meeting on one day for one person. The rest of the tool
works on occurrences, not on raw VEVENTs, so recurrence and multi-attendee
meetings are handled once here.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

from meetingtax.ics import VEvent

# Map an RFC 5545 weekday code to Python's Monday=0 weekday index.
_WEEKDAY_CODES = {
    "MO": 0,
    "TU": 1,
    "WE": 2,
    "TH": 3,
    "FR": 4,
    "SA": 5,
    "SU": 6,
}

# When a recurrence rule has no COUNT and no UNTIL, we refuse to expand forever.
# This bound keeps output finite and is recorded in the report and README.
_UNBOUNDED_LIMIT = 366


@dataclass(frozen=True)
class Occurrence:
    """One meeting instance with a resolved start and end."""

    uid: str
    summary: str
    attendee: str
    start: _dt.datetime
    end: _dt.datetime
    from_recurrence: bool = False

    @property
    def day(self) -> _dt.date:
        return self.start.date()

    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() // 60)


@dataclass
class SkippedRecurrence:
    """A recurrence this tool declined to expand, with the reason."""

    uid: str
    summary: str
    freq: str
    reason: str


@dataclass
class ExpansionResult:
    """Occurrences produced from a calendar plus any recurrences we skipped."""

    occurrences: list[Occurrence] = field(default_factory=list)
    skipped: list[SkippedRecurrence] = field(default_factory=list)


def _event_attendees(event: VEvent) -> list[str]:
    """Every distinct person on a meeting, organizer included, order preserved."""
    people: list[str] = []
    if event.organizer:
        people.append(event.organizer)
    for attendee in event.attendees:
        if attendee not in people:
            people.append(attendee)
    return people


def _base_dates(event: VEvent) -> list[_dt.datetime]:
    """The list of start datetimes an event produces, after any expansion.

    Non-recurring events yield a single start. DAILY and WEEKLY rules are
    expanded within their COUNT or UNTIL bound. Other rules are handled by the
    caller, which records them as skipped.
    """
    assert event.dtstart is not None
    start = event.dtstart.value
    rule = event.rrule
    if rule is None or not rule.expandable:
        return [start]

    starts: list[_dt.datetime] = []
    if rule.freq == "DAILY":
        step = _dt.timedelta(days=rule.interval)
        current = start
        emitted = 0
        limit = rule.count if rule.count is not None else _UNBOUNDED_LIMIT
        while emitted < limit:
            if rule.until is not None and current > rule.until:
                break
            starts.append(current)
            emitted += 1
            current = current + step
        return starts

    # WEEKLY
    weekdays = (
        [_WEEKDAY_CODES[d] for d in rule.byday if d in _WEEKDAY_CODES]
        if rule.byday
        else [start.weekday()]
    )
    weekdays = sorted(set(weekdays))
    week_start = start - _dt.timedelta(days=start.weekday())
    emitted = 0
    limit = rule.count if rule.count is not None else _UNBOUNDED_LIMIT
    week_index = 0
    while emitted < limit:
        base_week = week_start + _dt.timedelta(weeks=week_index * rule.interval)
        stop = False
        for wd in weekdays:
            candidate = base_week + _dt.timedelta(days=wd)
            candidate = candidate.replace(
                hour=start.hour, minute=start.minute, second=start.second
            )
            if candidate < start:
                continue
            if rule.until is not None and candidate > rule.until:
                stop = True
                break
            if emitted >= limit:
                stop = True
                break
            starts.append(candidate)
            emitted += 1
        if stop:
            break
        week_index += 1
        if week_index > _UNBOUNDED_LIMIT:
            break
    return starts


def expand(events: list[VEvent]) -> ExpansionResult:
    """Turn VEVENTs into per person per occurrence rows.

    Events without a start and end are dropped. Recurrence rules other than
    DAILY and WEEKLY are not expanded; the series is recorded in ``skipped`` and
    only its first instance is emitted.
    """
    result = ExpansionResult()
    for event in events:
        if event.dtstart is None or event.dtend is None:
            continue
        duration = event.dtend.value - event.dtstart.value
        people = _event_attendees(event)
        if not people:
            continue

        rule = event.rrule
        if rule is not None and not rule.expandable:
            result.skipped.append(
                SkippedRecurrence(
                    uid=event.uid,
                    summary=event.summary,
                    freq=rule.freq or "UNKNOWN",
                    reason=(
                        "FREQ=" + (rule.freq or "UNKNOWN") + " is not expanded; "
                        "only the first instance is counted"
                    ),
                )
            )

        for start in _base_dates(event):
            end = start + duration
            for person in people:
                result.occurrences.append(
                    Occurrence(
                        uid=event.uid,
                        summary=event.summary,
                        attendee=person,
                        start=start,
                        end=end,
                        from_recurrence=rule is not None and rule.expandable,
                    )
                )

    result.occurrences.sort(key=lambda o: (o.attendee, o.start, o.uid))
    result.skipped.sort(key=lambda s: (s.uid, s.summary))
    return result

# draft note 926
