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


@dataclass
class ParsedDateTime:
    """A date-time value with the timezone hint kept but not applied."""

    value: _dt.datetime
    is_utc: bool = False
    tzid: str | None = None
    date_only: bool = False


@dataclass
class RRule:
    """A recurrence rule reduced to the fields meetingtax understands."""

    freq: str
    interval: int = 1
    count: int | None = None
    until: _dt.datetime | None = None
    byday: list[str] = field(default_factory=list)
    raw: str = ""

    @property
    def expandable(self) -> bool:
        """True when this tool expands the rule rather than skipping it."""
        return self.freq in ("DAILY", "WEEKLY")


@dataclass
class VEvent:
    """A parsed VEVENT with the properties meetingtax reads."""

    uid: str
    summary: str
    dtstart: ParsedDateTime | None
    dtend: ParsedDateTime | None
    attendees: list[str] = field(default_factory=list)
    organizer: str | None = None
    rrule: RRule | None = None
    properties: dict[str, RawProperty] = field(default_factory=dict)

