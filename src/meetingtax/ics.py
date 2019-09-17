"""A small iCalendar (RFC 5545) reader scoped to what meetingtax needs.

This is not a full RFC 5545 implementation. It handles the parts that matter
for measuring meeting load:

- line unfolding (a line beginning with a space or tab continues the previous),
- property parameter parsing (``KEY;PARAM=VALUE:value``),
- text escaping in property values (``\\n``, ``\\,``, ``\\;``, ``\\\\``),
- DTSTART and DTEND both with a floating or UTC form and with a TZID parameter,
- the DURATION property as an alternative to DTEND,
- VEVENT extraction, ignoring VTODO, VJOURNAL, VFREEBUSY and VALARM,
- the RRULE property, parsed but expanded only for the daily and weekly cases.

Times are read as naive local wall-clock values. A trailing ``Z`` (UTC) and any
TZID parameter are recorded on the parsed value but not converted, because the
tool reasons about a person's day as they experience it on their own calendar.
The limitation is stated plainly in the README.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field


class ICSError(ValueError):
    """Raised when the input cannot be read as iCalendar."""


@dataclass
class RawProperty:
    """One unfolded content line split into name, parameters and value."""

    name: str
    params: dict[str, str]
    value: str

