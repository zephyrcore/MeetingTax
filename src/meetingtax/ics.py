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


def unfold_lines(text: str) -> list[str]:
    """Join continuation lines per RFC 5545 section 3.1.

    A CRLF followed by a single space or tab is a fold. We accept plain LF too,
    because exported files are not always strict about the carriage return.
    """
    normalised = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalised.split("\n")
    unfolded: list[str] = []
    for line in lines:
        if line[:1] in (" ", "\t") and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return unfolded


def _split_params(name_part: str) -> tuple[str, dict[str, str]]:
    """Split ``NAME;P1=v1;P2=v2`` into the name and a parameter map."""
    pieces = _split_unquoted(name_part, ";")
    name = pieces[0].upper()
    params: dict[str, str] = {}
    for piece in pieces[1:]:
        if "=" in piece:
            key, _, val = piece.partition("=")
            params[key.upper()] = val.strip('"')
    return name, params


def _split_unquoted(text: str, sep: str) -> list[str]:
    """Split on ``sep`` but ignore separators inside double quotes."""
    out: list[str] = []
    current: list[str] = []
    in_quote = False
    for ch in text:
        if ch == '"':
            in_quote = not in_quote
            current.append(ch)
        elif ch == sep and not in_quote:
            out.append("".join(current))
            current = []
