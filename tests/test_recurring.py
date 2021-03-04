"""Tests for recurring series analysis."""

import unittest

from meetingtax import ics
from meetingtax.recurring import analyse, stale_series


def _cal(body: str) -> list:
    return ics.parse_calendar("BEGIN:VCALENDAR\r\n" + body + "END:VCALENDAR\r\n")


class RecurringTests(unittest.TestCase):
    def test_weekly_series_is_stale(self):
        events = _cal(
            "BEGIN:VEVENT\r\n"
            "UID:w@x\r\n"
            "SUMMARY:Standup\r\n"
            "DTSTART:20260907T093000\r\n"
            "DTEND:20260907T100000\r\n"
            "ORGANIZER;CN=Ada:mailto:ada@x\r\n"
            "ATTENDEE;CN=Bao:mailto:bao@x\r\n"
            "RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=6\r\n"
            "END:VEVENT\r\n"
        )
        stale = stale_series(events)
