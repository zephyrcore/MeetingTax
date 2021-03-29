# Sample fixtures

`team-calendar.ics` is a hand authored iCalendar test vector, not exported from
any real calendar. It exists to exercise every path meetingtax cares about. No
real person, address, or organisation is involved. The addresses use the
`example.org` reserved domain.

## What it contains

Three people appear as organizers and attendees: Ada Lovelace, Bao Nguyen, and
Chen Wei.

- A fragmented day for Ada on 2026-09-07: six short meetings scattered from
  09:00 to 16:00 so that no free stretch reaches two hours.
- A protected day on 2026-09-08: a single short meeting leaves a long
  uninterrupted block.
- Meetings that fill exact 30 and 60 minute slots, so the load report can count
  meetings that could plausibly have been shorter.
- A DTSTART and DTEND carrying a `TZID=America/New_York` parameter, to show that
  the tool records the timezone hint but reads the wall-clock value.
- A folded SUMMARY line (a value continued onto a second line with a leading
  space), to exercise line unfolding.
