"""Line oriented report formatting.

Every function here returns a list of strings, one per output line, so results
diff cleanly in git and are byte identical for identical input. No wall-clock
time and no randomness enter the output.
"""

from __future__ import annotations

import datetime as _dt

from meetingtax.events import ExpansionResult, Occurrence
from meetingtax.fragments import PersonFocus, Workday


def _fmt_hm(minutes: int) -> str:
    """Render a minute count as ``HhMM`` such as ``3h05`` or ``0h30``."""
    hours = minutes // 60
    mins = minutes % 60
    return str(hours) + "h" + str(mins).zfill(2)


def _fmt_time(value: _dt.datetime) -> str:
    return value.strftime("%H:%M")


def load_report(
    result: ExpansionResult,
    workday: Workday,
) -> list[str]:
    """Summarise the whole calendar: hours, short meetings, skipped rules."""
    occ = result.occurrences
    lines: list[str] = []
    lines.append("meetingtax load report")
    lines.append("workday window: " + _window_label(workday))
    lines.append("")

    total_person_minutes = sum(o.duration_minutes for o in occ)
    unique_meetings = _unique_meeting_slots(occ)
    lines.append("occurrences (person instances): " + str(len(occ)))
    lines.append("distinct meeting slots: " + str(len(unique_meetings)))
    lines.append("total person meeting hours: " + _fmt_hm(total_person_minutes))

    shorter = _could_be_shorter(unique_meetings)
    lines.append("meetings longer than 25 minutes ending on the hour or half: "
                 + str(len(shorter)))
    lines.append("")

    lines.append("people seen: " + str(len({o.attendee for o in occ})))
    for person in sorted({o.attendee for o in occ}):
        p_minutes = sum(o.duration_minutes for o in occ if o.attendee == person)
        lines.append("  " + person + ": " + _fmt_hm(p_minutes))
    lines.append("")

    if result.skipped:
        lines.append("recurrence rules not expanded: " + str(len(result.skipped)))
        for skip in result.skipped:
            lines.append("  " + skip.uid + " (" + skip.freq + "): " + skip.reason)
    else:
        lines.append("recurrence rules not expanded: 0")
    return lines


def _window_label(workday: Workday) -> str:
    start = str(workday.start_hour).zfill(2) + ":" + str(workday.start_minute).zfill(2)
    end = str(workday.end_hour).zfill(2) + ":" + str(workday.end_minute).zfill(2)
    return start + " to " + end


def _unique_meeting_slots(
    occurrences: list[Occurrence],
) -> list[tuple[str, _dt.datetime, _dt.datetime]]:
    """Collapse per person rows back to one row per meeting instance."""
    seen: dict[tuple[str, _dt.datetime], tuple[str, _dt.datetime, _dt.datetime]] = {}
    for o in occurrences:
        key = (o.uid, o.start)
        if key not in seen:
            seen[key] = (o.uid, o.start, o.end)
    return [seen[k] for k in sorted(seen)]


def _could_be_shorter(
    slots: list[tuple[str, _dt.datetime, _dt.datetime]],
) -> list[tuple[str, _dt.datetime, _dt.datetime]]:
    """Meetings that fill a standard slot and could plausibly be trimmed.

    A meeting of more than 25 minutes whose length is an exact multiple of 30 is
    treated as booked to a calendar slot rather than to the work it needs. This
    is a heuristic, stated as such in the README, not a claim about any single
    meeting.
    """
    out = []
    for uid, start, end in slots:
        minutes = int((end - start).total_seconds() // 60)
        if minutes > 25 and minutes % 30 == 0:
            out.append((uid, start, end))
    return out


def focus_report(
    people: list[PersonFocus],
    workday: Workday,
    threshold_minutes: int,
) -> list[str]:
    """Per person per day longest focus block against the threshold."""
    lines: list[str] = []
    lines.append("meetingtax focus report")
    lines.append("workday window: " + _window_label(workday))
    lines.append("focus threshold: " + _fmt_hm(threshold_minutes))
    lines.append("")

    for person in people:
        lines.append(person.attendee)
        for day in person.days:
            block = day.longest_free_block
            if block is None:
                span = "none"
            else:
                span = _fmt_time(block[0]) + " to " + _fmt_time(block[1])
            flag = "FRAGMENTED" if day.longest_free_minutes < threshold_minutes else "ok"
