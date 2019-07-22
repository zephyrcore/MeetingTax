"""Per person per day free block computation.

The workday is a fixed window (default 09:00 to 17:00). Meetings carve busy
intervals out of it. What is left are free blocks. The longest free block is the
best uninterrupted stretch a person could have used for focused work that day.

A day of six scattered half hour meetings leaves many short gaps and no long
one. A day with a single block leaves one long stretch. This module makes that
difference a number.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

from meetingtax.events import Occurrence

