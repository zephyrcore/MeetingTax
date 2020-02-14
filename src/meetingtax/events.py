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


