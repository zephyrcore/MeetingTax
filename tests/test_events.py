"""Tests for occurrence expansion."""

import datetime as dt
import unittest

from meetingtax import ics
from meetingtax.events import expand


def _cal(body: str) -> list:
    return ics.parse_calendar("BEGIN:VCALENDAR\r\n" + body + "END:VCALENDAR\r\n")


class ExpandTests(unittest.TestCase):
    def test_single_meeting_expands_per_attendee(self):
        events = _cal(
            "BEGIN:VEVENT\r\n"
            "UID:m@x\r\n"
            "SUMMARY:Sync\r\n"
            "DTSTART:20260907T090000\r\n"
            "DTEND:20260907T093000\r\n"
            "ORGANIZER;CN=Ada:mailto:ada@x\r\n"
            "ATTENDEE;CN=Bao:mailto:bao@x\r\n"
            "END:VEVENT\r\n"
        )
        result = expand(events)
        people = {o.attendee for o in result.occurrences}
        self.assertEqual(people, {"Ada", "Bao"})
        self.assertEqual(len(result.occurrences), 2)

    def test_weekly_rule_expands_by_count(self):
        events = _cal(
            "BEGIN:VEVENT\r\n"
            "UID:w@x\r\n"
            "SUMMARY:Standup\r\n"
            "DTSTART:20260907T090000\r\n"
            "DTEND:20260907T093000\r\n"
            "ORGANIZER;CN=Ada:mailto:ada@x\r\n"
            "RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=3\r\n"
            "END:VEVENT\r\n"
        )
        result = expand(events)
        days = sorted({o.day for o in result.occurrences})
        self.assertEqual(
            days,
            [dt.date(2026, 9, 7), dt.date(2026, 9, 14), dt.date(2026, 9, 21)],
        )

    def test_daily_rule_expands_by_count(self):
        events = _cal(
            "BEGIN:VEVENT\r\n"
            "UID:d@x\r\n"
            "SUMMARY:Daily\r\n"
            "DTSTART:20260907T090000\r\n"
            "DTEND:20260907T091500\r\n"
            "ORGANIZER;CN=Ada:mailto:ada@x\r\n"
            "RRULE:FREQ=DAILY;COUNT=4\r\n"
            "END:VEVENT\r\n"
        )
        result = expand(events)
        self.assertEqual(len({o.day for o in result.occurrences}), 4)

    def test_unsupported_rule_is_skipped_but_first_kept(self):
        events = _cal(
