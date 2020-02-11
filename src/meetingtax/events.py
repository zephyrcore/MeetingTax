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
