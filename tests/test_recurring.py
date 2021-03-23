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
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0].freq, "WEEKLY")
        self.assertEqual(stale[0].duration_minutes, 30)
        self.assertEqual(stale[0].attendee_count, 2)

    def test_monthly_series_not_judged(self):
        events = _cal(
            "BEGIN:VEVENT\r\n"
            "UID:m@x\r\n"
            "SUMMARY:Monthly\r\n"
            "DTSTART:20260907T140000\r\n"
            "DTEND:20260907T150000\r\n"
            "ORGANIZER;CN=Ada:mailto:ada@x\r\n"
            "RRULE:FREQ=MONTHLY;COUNT=4\r\n"
            "END:VEVENT\r\n"
        )
        series = analyse(events)
        self.assertEqual(len(series), 1)
        self.assertFalse(series[0].stale)
        self.assertFalse(series[0].expanded)

    def test_non_recurring_ignored(self):
        events = _cal(
            "BEGIN:VEVENT\r\n"
            "UID:o@x\r\n"
