"""Tests for the iCalendar reader."""

import datetime as dt
import unittest

from meetingtax import ics


class UnfoldTests(unittest.TestCase):
    def test_space_continuation_joins(self):
        text = "SUMMARY:long value that\r\n continues here"
        self.assertEqual(ics.unfold_lines(text), ["SUMMARY:long value thatcontinues here"])

    def test_tab_continuation_joins(self):
