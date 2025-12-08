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

    def test_single_block_leaves_long_free(self):
        occs = [_occ("Ada", 9, 0, 10, 0)]
        focus = compute_day("Ada", dt.date(2026, 9, 7), occs, self.workday)
        self.assertEqual(focus.longest_free_minutes, 420)

    def test_scattered_meetings_fragment_the_day(self):
        occs = [
            _occ("Ada", 9, 0, 9, 30),
            _occ("Ada", 10, 0, 10, 30),
            _occ("Ada", 11, 0, 11, 30),
            _occ("Ada", 13, 0, 13, 30),
            _occ("Ada", 14, 0, 14, 30),
            _occ("Ada", 15, 30, 16, 0),
        ]
        focus = compute_day("Ada", dt.date(2026, 9, 7), occs, self.workday)
        # Longest gap is 13:30 to 14:00 is 30, 11:30 to 13:00 is 90, 16:00 to
        # 17:00 is 60. The longest is 90 minutes.
        self.assertEqual(focus.longest_free_minutes, 90)

    def test_overlapping_meetings_merge(self):
        occs = [_occ("Ada", 9, 0, 10, 0), _occ("Ada", 9, 30, 11, 0)]
        focus = compute_day("Ada", dt.date(2026, 9, 7), occs, self.workday)
        self.assertEqual(focus.busy_minutes, 120)

    def test_meeting_outside_window_ignored(self):
        occs = [_occ("Ada", 7, 0, 8, 0)]
        focus = compute_day("Ada", dt.date(2026, 9, 7), occs, self.workday)
        self.assertEqual(focus.longest_free_minutes, 480)


class SummariseTests(unittest.TestCase):
    def test_fragmented_days_counted_against_threshold(self):
        occs_frag = [
            _occ("Ada", 9, 0, 9, 30),
            _occ("Ada", 10, 0, 10, 30),
            _occ("Ada", 11, 0, 11, 30),
            _occ("Ada", 13, 0, 13, 30),
            _occ("Ada", 14, 0, 14, 30),
            _occ("Ada", 15, 30, 16, 0),
        ]
        occs_clear = [_occ("Ada", 9, 0, 9, 30, day=dt.date(2026, 9, 8))]
        days = compute_all(occs_frag + occs_clear, Workday())
        people = summarise_people(days, threshold_minutes=120)
        ada = people[0]
        self.assertEqual(ada.fragmented_days, 1)
        self.assertEqual(ada.best_longest_free_minutes, 450)


if __name__ == "__main__":
    unittest.main()
