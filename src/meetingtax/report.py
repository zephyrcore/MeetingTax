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
