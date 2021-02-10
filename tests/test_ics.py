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
    def test_params_parsed(self):
        prop = ics.parse_property("DTSTART;TZID=America/New_York:20260908T090000")
        self.assertEqual(prop.name, "DTSTART")
        self.assertEqual(prop.params["TZID"], "America/New_York")
        self.assertEqual(prop.value, "20260908T090000")

    def test_quoted_param_value_keeps_colon(self):
        prop = ics.parse_property('X-THING;CN="Doe, Jane":value')
        self.assertEqual(prop.params["CN"], "Doe, Jane")
