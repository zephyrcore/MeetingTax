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
import sys

from meetingtax import __version__
from meetingtax import report as report_mod
from meetingtax.events import expand
from meetingtax.fragments import Workday, compute_all, summarise_people
from meetingtax.ics import ICSError, parse_calendar
from meetingtax.recurring import analyse

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2


def _parse_hhmm(value: str) -> tuple[int, int]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("time must be HH:MM, got " + value)
    hh, _, mm = value.partition(":")
    try:
        hour, minute = int(hh), int(mm)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("time must be HH:MM, got " + value) from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise argparse.ArgumentTypeError("time out of range: " + value)
    return hour, minute


def _read_calendar(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    return parse_calendar(text)


def _workday_from_args(args) -> Workday:
    sh, sm = args.day_start
    eh, em = args.day_end
    return Workday(start_hour=sh, start_minute=sm, end_hour=eh, end_minute=em)


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("calendar", help="path to an .ics file")
    parser.add_argument(
        "--day-start",
        type=_parse_hhmm,
        default=(9, 0),
        metavar="HH:MM",
        help="start of the workday window, default 09:00",
    )
    parser.add_argument(
        "--day-end",
        type=_parse_hhmm,
        default=(17, 0),
        metavar="HH:MM",
        help="end of the workday window, default 17:00",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
