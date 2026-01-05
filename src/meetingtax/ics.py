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
        else:
            current.append(ch)
    out.append("".join(current))
    return out


def parse_property(line: str) -> RawProperty | None:
    """Parse one unfolded content line into a RawProperty, or None if blank."""
    if not line.strip():
        return None
    if ":" not in line:
        raise ICSError("content line has no value separator: " + line[:40])
    name_part, _, value = line.partition(":")
    name, params = _split_params(name_part)
    return RawProperty(name=name, params=params, value=value)


def unescape_text(value: str) -> str:
    """Reverse RFC 5545 TEXT escaping."""
    out: list[str] = []
    i = 0
    while i < len(value):
        ch = value[i]
        if ch == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            if nxt in ("n", "N"):
                out.append("\n")
            elif nxt in (",", ";", "\\"):
                out.append(nxt)
            else:
                out.append(nxt)
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def parse_datetime(prop: RawProperty) -> ParsedDateTime:
    """Read a DATE or DATE-TIME value, keeping the timezone hint.

    Accepts the basic forms ``20260907T090000`` (floating), ``...Z`` (UTC), and
    a VALUE=DATE form ``20260907``. A TZID parameter is recorded but not applied.
    """
    raw = prop.value.strip()
    tzid = prop.params.get("TZID")
    value_type = prop.params.get("VALUE", "").upper()

    if value_type == "DATE" or (len(raw) == 8 and "T" not in raw):
        try:
            parsed = _dt.datetime.strptime(raw, "%Y%m%d")
        except ValueError as exc:
            raise ICSError("bad DATE value: " + raw) from exc
        return ParsedDateTime(value=parsed, tzid=tzid, date_only=True)

    is_utc = raw.endswith("Z")
    core = raw[:-1] if is_utc else raw
    try:
        parsed = _dt.datetime.strptime(core, "%Y%m%dT%H%M%S")
    except ValueError as exc:
        raise ICSError("bad DATE-TIME value: " + raw) from exc
    return ParsedDateTime(value=parsed, is_utc=is_utc, tzid=tzid)


def parse_duration(value: str) -> _dt.timedelta:
    """Parse an RFC 5545 DURATION such as ``PT1H30M`` or ``P1D``.

    Weeks, days, hours, minutes and seconds are supported. A leading minus sign
    negates the whole duration.
    """
    text = value.strip()
    sign = 1
    if text.startswith("-"):
        sign = -1
        text = text[1:]
    elif text.startswith("+"):
        text = text[1:]
    if not text.startswith("P"):
        raise ICSError("bad DURATION value: " + value)
    text = text[1:]

    weeks = days = hours = minutes = seconds = 0
    number = ""
    in_time = False
    for ch in text:
        if ch == "T":
            in_time = True
            continue
        if ch.isdigit():
            number += ch
            continue
        if not number:
            raise ICSError("bad DURATION value: " + value)
        amount = int(number)
        number = ""
        if ch == "W":
            weeks = amount
        elif ch == "D":
            days = amount
        elif ch == "H" and in_time:
            hours = amount
        elif ch == "M" and in_time:
            minutes = amount
        elif ch == "S" and in_time:
            seconds = amount
        else:
            raise ICSError("unsupported DURATION unit in: " + value)
    delta = _dt.timedelta(
        weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds
    )
    return sign * delta


def parse_rrule(value: str) -> RRule:
    """Parse an RRULE property value into an RRule.

    FREQ, INTERVAL, COUNT, UNTIL and BYDAY are read. Anything else is preserved
    on ``raw`` and ignored during expansion.
    """
    parts = {}
    for token in value.split(";"):
        if "=" in token:
            key, _, val = token.partition("=")
            parts[key.upper()] = val
    freq = parts.get("FREQ", "").upper()
    interval = int(parts.get("INTERVAL", "1") or "1")
    count = int(parts["COUNT"]) if "COUNT" in parts else None
    until = None
    if "UNTIL" in parts:
        raw_until = parts["UNTIL"]
        core = raw_until[:-1] if raw_until.endswith("Z") else raw_until
        try:
            if "T" in core:
                until = _dt.datetime.strptime(core, "%Y%m%dT%H%M%S")
            else:
                until = _dt.datetime.strptime(core, "%Y%m%d")
        except ValueError as exc:
            raise ICSError("bad UNTIL in RRULE: " + raw_until) from exc
    byday = [d.strip().upper() for d in parts.get("BYDAY", "").split(",") if d.strip()]
    return RRule(
        freq=freq,
        interval=interval,
        count=count,
        until=until,
        byday=byday,
        raw=value,
    )


def _clean_calendar_address(value: str, params: dict[str, str]) -> str:
    """Prefer a CN parameter, otherwise strip a mailto prefix from the value."""
    cn = params.get("CN")
    if cn:
        return cn
    addr = value.strip()
    if addr.upper().startswith("MAILTO:"):
        addr = addr[len("MAILTO:"):]
    return addr


def parse_calendar(text: str) -> list[VEvent]:
    """Parse an iCalendar document and return every VEVENT it contains."""
    lines = unfold_lines(text)
    events: list[VEvent] = []
    in_event = False
    depth_other = 0

    uid = summary = ""
    dtstart = dtend = None
    attendees: list[str] = []
    organizer: str | None = None
    rrule: RRule | None = None
    duration: _dt.timedelta | None = None
    props: dict[str, RawProperty] = {}

    def reset() -> None:
        nonlocal uid, summary, dtstart, dtend, attendees, organizer, rrule
        nonlocal duration, props
        uid = summary = ""
        dtstart = dtend = None
        attendees = []
        organizer = None
        rrule = None
        duration = None
        props = {}

    for line in lines:
        prop = parse_property(line)
        if prop is None:
            continue

        if prop.name == "BEGIN":
            block = prop.value.upper()
            if block == "VEVENT" and depth_other == 0:
                in_event = True
                reset()
            elif in_event:
                depth_other += 1
            continue

        if prop.name == "END":
            block = prop.value.upper()
            if block == "VEVENT" and in_event and depth_other == 0:
                if dtstart is not None and dtend is None and duration is not None:
                    dtend = ParsedDateTime(
                        value=dtstart.value + duration,
                        is_utc=dtstart.is_utc,
                        tzid=dtstart.tzid,
                    )
                events.append(
                    VEvent(
                        uid=uid,
                        summary=summary,
                        dtstart=dtstart,
                        dtend=dtend,
                        attendees=list(attendees),
                        organizer=organizer,
                        rrule=rrule,
                        properties=dict(props),
                    )
                )
                in_event = False
            elif in_event and depth_other > 0:
                depth_other -= 1
            continue

        if not in_event or depth_other > 0:
            continue

        props[prop.name] = prop
        if prop.name == "UID":
            uid = prop.value.strip()
        elif prop.name == "SUMMARY":
            summary = unescape_text(prop.value)
        elif prop.name == "DTSTART":
            dtstart = parse_datetime(prop)
        elif prop.name == "DTEND":
            dtend = parse_datetime(prop)
        elif prop.name == "DURATION":
            duration = parse_duration(prop.value)
        elif prop.name == "ATTENDEE":
            attendees.append(_clean_calendar_address(prop.value, prop.params))
        elif prop.name == "ORGANIZER":
            organizer = _clean_calendar_address(prop.value, prop.params)
        elif prop.name == "RRULE":
            rrule = parse_rrule(prop.value)

    if in_event:
        raise ICSError("VEVENT was opened but never closed with END:VEVENT")

    return events

# draft note 903
