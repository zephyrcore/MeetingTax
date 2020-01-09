"""Command line interface for meetingtax.

Subcommands:
  load       parse a calendar and report meeting load and skipped rules
  focus      report per person per day longest focus block against a threshold
  recurring  list recurring series and flag the stale ones
  version    print the package version

Exit codes: 0 clean, 1 findings present, 2 usage error.
"""

from __future__ import annotations

import argparse
