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
        prog="meetingtax",
        description="Measure the attention cost of meetings from an iCalendar export.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_load = sub.add_parser("load", help="report meeting load and skipped rules")
    _add_common(p_load)

    p_focus = sub.add_parser("focus", help="report focus fragmentation per person")
    _add_common(p_focus)
    p_focus.add_argument(
        "--threshold",
        type=int,
        default=120,
        metavar="MINUTES",
        help="declared focus block threshold in minutes, default 120",
    )

    p_recurring = sub.add_parser("recurring", help="flag stale recurring series")
    p_recurring.add_argument("calendar", help="path to an .ics file")

    sub.add_parser("version", help="print the version and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        print("meetingtax " + __version__)
        return EXIT_CLEAN

    try:
        events = _read_calendar(args.calendar)
    except FileNotFoundError:
        print("error: file not found: " + args.calendar, file=sys.stderr)
        return EXIT_USAGE
    except ICSError as exc:
        print("error: " + str(exc), file=sys.stderr)
        return EXIT_USAGE

    if args.command == "load":
        workday = _workday_from_args(args)
        result = expand(events)
        for line in report_mod.load_report(result, workday):
            print(line)
        return EXIT_FINDINGS if result.skipped else EXIT_CLEAN

    if args.command == "focus":
        workday = _workday_from_args(args)
        result = expand(events)
        days = compute_all(result.occurrences, workday)
        people = summarise_people(days, args.threshold)
        for line in report_mod.focus_report(people, workday, args.threshold):
            print(line)
        fragmented = sum(p.fragmented_days for p in people)
        return EXIT_FINDINGS if fragmented else EXIT_CLEAN

    if args.command == "recurring":
        series = analyse(events)
        for line in report_mod.recurring_report(series):
            print(line)
        stale = sum(1 for s in series if s.stale)
        return EXIT_FINDINGS if stale else EXIT_CLEAN

    parser.print_usage(sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())

# draft note 921
