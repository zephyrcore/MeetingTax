"""Tests for free block computation."""

import datetime as dt
import unittest

from meetingtax.events import Occurrence
from meetingtax.fragments import Workday, compute_day, compute_all, summarise_people
