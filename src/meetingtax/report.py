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

