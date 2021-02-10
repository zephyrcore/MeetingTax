"""Tests for the iCalendar reader."""

import datetime as dt
import unittest

from meetingtax import ics


class UnfoldTests(unittest.TestCase):
    def test_space_continuation_joins(self):
        text = "SUMMARY:long value that\r\n continues here"
        self.assertEqual(ics.unfold_lines(text), ["SUMMARY:long value thatcontinues here"])

    def test_tab_continuation_joins(self):
        text = "DESC:first\n\tsecond"
        self.assertEqual(ics.unfold_lines(text), ["DESC:firstsecond"])

    def test_plain_lines_kept(self):
        text = "A:1\nB:2"
        self.assertEqual(ics.unfold_lines(text), ["A:1", "B:2"])


class PropertyTests(unittest.TestCase):
