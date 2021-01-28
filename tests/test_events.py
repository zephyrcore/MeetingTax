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
