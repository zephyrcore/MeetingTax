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

    def test_missing_separator_raises(self):
        with self.assertRaises(ics.ICSError):
            ics.parse_property("NOVALUE")


class EscapingTests(unittest.TestCase):
    def test_escaped_comma_and_newline(self):
        self.assertEqual(ics.unescape_text("a\\, b\\nc"), "a, b\nc")

    def test_escaped_backslash(self):
        self.assertEqual(ics.unescape_text("a\\\\b"), "a\\b")


class DateTimeTests(unittest.TestCase):
    def test_floating_datetime(self):
        prop = ics.parse_property("DTSTART:20260907T090000")
        parsed = ics.parse_datetime(prop)
        self.assertEqual(parsed.value, dt.datetime(2026, 9, 7, 9, 0, 0))
        self.assertFalse(parsed.is_utc)
        self.assertIsNone(parsed.tzid)

    def test_utc_datetime(self):
        prop = ics.parse_property("DTSTART:20260907T090000Z")
        parsed = ics.parse_datetime(prop)
        self.assertTrue(parsed.is_utc)
        self.assertEqual(parsed.value, dt.datetime(2026, 9, 7, 9, 0, 0))

    def test_tzid_recorded_not_applied(self):
        prop = ics.parse_property("DTSTART;TZID=America/New_York:20260908T090000")
        parsed = ics.parse_datetime(prop)
        self.assertEqual(parsed.tzid, "America/New_York")
        self.assertEqual(parsed.value, dt.datetime(2026, 9, 8, 9, 0, 0))

    def test_date_only(self):
        prop = ics.parse_property("DTSTART;VALUE=DATE:20260908")
        parsed = ics.parse_datetime(prop)
        self.assertTrue(parsed.date_only)
        self.assertEqual(parsed.value, dt.datetime(2026, 9, 8, 0, 0, 0))


class DurationTests(unittest.TestCase):
    def test_hours_minutes(self):
        self.assertEqual(ics.parse_duration("PT1H30M"), dt.timedelta(hours=1, minutes=30))

    def test_days(self):
        self.assertEqual(ics.parse_duration("P2D"), dt.timedelta(days=2))

    def test_negative(self):
        self.assertEqual(ics.parse_duration("-PT15M"), dt.timedelta(minutes=-15))

    def test_bad_value_raises(self):
        with self.assertRaises(ics.ICSError):
            ics.parse_duration("90m")


class RRuleTests(unittest.TestCase):
    def test_weekly_with_byday(self):
        rule = ics.parse_rrule("FREQ=WEEKLY;BYDAY=MO,WE;COUNT=6")
        self.assertEqual(rule.freq, "WEEKLY")
        self.assertEqual(rule.count, 6)
        self.assertEqual(rule.byday, ["MO", "WE"])
        self.assertTrue(rule.expandable)

    def test_monthly_not_expandable(self):
        rule = ics.parse_rrule("FREQ=MONTHLY;COUNT=4")
        self.assertFalse(rule.expandable)

    def test_until_parsed(self):
        rule = ics.parse_rrule("FREQ=DAILY;UNTIL=20260910T090000Z")
        self.assertEqual(rule.until, dt.datetime(2026, 9, 10, 9, 0, 0))


