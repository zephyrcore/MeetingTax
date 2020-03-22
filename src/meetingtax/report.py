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
