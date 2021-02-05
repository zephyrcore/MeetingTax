"""Tests for free block computation."""

import datetime as dt
import unittest

from meetingtax.events import Occurrence
from meetingtax.fragments import Workday, compute_day, compute_all, summarise_people


def _occ(attendee, sh, sm, eh, em, day=dt.date(2026, 9, 7)):
    start = dt.datetime(day.year, day.month, day.day, sh, sm)
    end = dt.datetime(day.year, day.month, day.day, eh, em)
    return Occurrence(uid="u", summary="s", attendee=attendee, start=start, end=end)


class ComputeDayTests(unittest.TestCase):
    def setUp(self):
        self.workday = Workday()

    def test_empty_day_is_one_full_block(self):
        focus = compute_day("Ada", dt.date(2026, 9, 7), [], self.workday)
        self.assertEqual(focus.longest_free_minutes, 480)

