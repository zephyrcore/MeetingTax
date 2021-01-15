"""Tests for occurrence expansion."""

import datetime as dt
import unittest

from meetingtax import ics
from meetingtax.events import expand


def _cal(body: str) -> list:
