"""Tests for recurring series analysis."""

import unittest

from meetingtax import ics
from meetingtax.recurring import analyse, stale_series


def _cal(body: str) -> list:
    return ics.parse_calendar("BEGIN:VCALENDAR\r\n" + body + "END:VCALENDAR\r\n")

