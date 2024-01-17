# Changelog

All notable changes to this project are recorded here.

## 0.1.0 - 2026-09-02

Initial release.

- iCalendar reader with line unfolding, TEXT escaping, DATE and DATE-TIME
  parsing with and without a TZID parameter, DURATION parsing, and VEVENT
  extraction.
- RRULE support for the DAILY and WEEKLY cases with COUNT, INTERVAL, UNTIL and
  BYDAY. Other frequencies are reported as skipped rather than mishandled.
- Focus fragmentation: per person per day longest free block within a workday
  window, and a count of days below a declared threshold.
- Recurring series analysis that flags standing invites whose shape never
  changes.
- CLI subcommands: load, focus, recurring, version.
- Exit codes: 0 clean, 1 findings present, 2 usage error.
- Hand authored sample fixture with a fragmented day, a protected day, and a
  stale weekly recurring meeting.
- A focus fragmentation data graphic and a wordmark logo.

<!-- draft note 522 -->
