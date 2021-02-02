"""Tests for free block computation."""

import datetime as dt
import unittest

from meetingtax.events import Occurrence
from meetingtax.fragments import Workday, compute_day, compute_all, summarise_people


def _occ(attendee, sh, sm, eh, em, day=dt.date(2026, 9, 7)):
    start = dt.datetime(day.year, day.month, day.day, sh, sm)
    end = dt.datetime(day.year, day.month, day.day, eh, em)
