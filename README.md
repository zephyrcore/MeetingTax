<table border="0">
<tr>
<td>

# meetingtax

meetingtax reads a calendar export in iCalendar format and measures what
meetings cost a team in attention, not only in hours. It reports total meeting
hours, meetings that could have been shorter, stale recurring invites, and above
all how badly each person's day is fragmented.

</td>
<td>

<img src="docs/assets/logo.svg" width="200"
 alt="meetingtax wordmark with meeting in slate and tax in green above a day strip of meeting cells and one free block" />

</td>
</tr>
</table>

An hour lost to a meeting is an hour. An hour of focus split into four pieces by
meetings scattered through the day is worth far less than an uninterrupted hour,
because the cost of context switching is real and it does not show up in a total
of booked hours. meetingtax exists to make that hidden cost visible. It takes the
`.ics` file your calendar can export and answers a plain question for each
person: what was the longest stretch of the workday you could actually have
concentrated, and how many days did that stretch never reach a length you
declared as the minimum for real work.

## Contents

- [The problem](#the-problem)
- [What it measures](#what-it-measures)
- [Install](#install)
- [Quick start](#quick-start)
- [The three reports](#the-three-reports)
- [Output fields](#output-fields)
- [A worked walkthrough](#a-worked-walkthrough)
- [How focus fragmentation is computed](#how-focus-fragmentation-is-computed)
- [Reading the focus report](#reading-the-focus-report)
- [Recurrence support and its honest limits](#recurrence-support-and-its-honest-limits)
- [Exit codes](#exit-codes)
- [Design decisions](#design-decisions)
- [Repository layout](#repository-layout)
- [Glossary](#glossary)
- [Integration notes](#integration-notes)
- [Verification](#verification)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [License](#license)

## The problem

You suspect meetings are eating your team, but the only number anyone can quote
is the total hours booked. That number hides the shape of the day. Consider two
people who each spend three hours in meetings. The first has a single three hour
block in the morning and a clear afternoon. The second has six half hour
meetings sprinkled from nine to four, each one landing in the middle of whatever
they were trying to do. Both show three hours of meetings on a report that
counts hours. Only one of them had a chance to do focused work.

The second person paid a tax that the hours total never records. Every meeting
carries a setup and teardown cost around it: the few minutes before to prepare,
the longer stretch after to recover the thread of the interrupted work. A day
diced into small pieces is nearly useless for anything that needs sustained
attention, even when the raw meeting hours look modest.

meetingtax measures the shape, not just the total. It finds the longest
uninterrupted free block each person had on each day, compares it against a
threshold you declare, and counts the days that fall short. It also surfaces the
two habits that quietly generate fragmentation: meetings booked to a round slot
that did not need the whole slot, and standing recurring invites that nobody has
revisited since they were created.

## What it measures

meetingtax reports four things.

1. Total meeting hours across everyone, and per person.
2. The count of meetings that fill a standard slot and could plausibly have been
   shorter.
3. Recurring meetings whose attendee set and duration never change across the
   series.
4. Focus time fragmentation: the longest uninterrupted free block per person per
   day, and how many days have no block longer than a declared threshold.

The fourth is the one the tool is built around. The first three are the context
that explains it.

## Install

meetingtax targets Python 3.11 and uses only the standard library. There are no
third party runtime dependencies and the code makes no network calls.

You can run it straight from a checkout without installing anything, by putting
the `src` directory on the path:

```
PYTHONPATH=src python -m meetingtax version
```

Or install it so the `meetingtax` console script is on your path:

```
pip install .
```

## Quick start

Run the load report against the bundled sample:

```
PYTHONPATH=src python -m meetingtax load samples/team-calendar.ics
```

```
meetingtax load report
workday window: 09:00 to 17:00

occurrences (person instances): 33
distinct meeting slots: 17
total person meeting hours: 19h00
meetings longer than 25 minutes ending on the hour or half: 17

people seen: 3
  Ada Lovelace: 7h30
  Bao Nguyen: 6h30
  Chen Wei: 5h00

recurrence rules not expanded: 1
  monthly-review@meetingtax.example (MONTHLY): FREQ=MONTHLY is not expanded; only the first instance is counted
```

## The three reports

Each report reads the same `.ics` file and answers a different question.

The `load` report is the overview: how much meeting time exists, how many
distinct meetings there are once recurrence is expanded, how it splits across
people, and which recurrence rules the tool declined to expand.

The `focus` report is the heart of the tool: per person, per day, the longest
free block and whether it cleared the threshold.

The `recurring` report lists every recurring series and marks the stale ones.

## Output fields

The `load` report fields, in order.

| Field | Meaning |
| --- | --- |
| occurrences (person instances) | One row per person per meeting instance after recurrence expansion. |
| distinct meeting slots | Meeting instances counted once, ignoring how many people attend. |
| total person meeting hours | Sum of every person instance duration, so a one hour meeting with three people is three person hours. |
| meetings longer than 25 minutes ending on the hour or half | Count of distinct slots that look booked to a round slot rather than to the work. |
| people seen | Number of distinct organizers and attendees. |
| per person hours | Each person's own share of person meeting hours. |
| recurrence rules not expanded | Series whose FREQ this tool does not expand, listed with the reason. |

The `focus` report fields, per day line.

| Field | Meaning |
| --- | --- |
| date | The calendar day in ISO form. |
| meetings | Number of meeting instances that touch this person on this day. |
| longest | The longest uninterrupted free block inside the workday window, as HhMM. |
| block | The clock span of that longest free block, or `none` if there is no free time. |
| flag | `FRAGMENTED` when the longest block is below the threshold, `ok` otherwise. |

The `recurring` report fields, per series line.

| Field | Meaning |
| --- | --- |
| uid | The VEVENT UID of the series. |
| freq and interval | The recurrence frequency and interval from the RRULE. |
| attendees | Number of distinct people on the series. |
| duration | The length of one instance, as HhMM. |
| state | `STALE` for an expanded repeating series, `skipped` for a rule not expanded, `ok` otherwise. |

## A worked walkthrough

Follow Ada through the sample. Her fragmented day is 2026-09-07. The source file
gives her these meetings that day, once the weekly standup is expanded onto the
Monday:

- 09:00 to 09:30 Standup sync
- 09:30 to 10:00 Weekly team standup
- 10:00 to 10:30 Design review
- 11:00 to 11:30 Vendor call
- 13:00 to 13:30 One to one
- 14:00 to 14:30 Roadmap check, part two
- 14:00 to 15:00 Monthly business review (first instance, organized by Chen)
- 15:30 to 16:00 Incident retro

The tool clips these to the 09:00 to 17:00 window, merges any overlaps, and
walks the gaps. The busy time runs solid from 09:00 to 10:30, then there are
short gaps and short meetings through the afternoon. The longest gap that
survives is 11:30 to 13:00, which is 90 minutes. That is Ada's longest focus
block for the day.

Run the focus report and Ada's Monday line reads:

```
  2026-09-07  meetings=8  longest=1h30  block=11:30 to 13:00  FRAGMENTED
```

Ninety minutes is below the declared threshold of 120, so the day is flagged
FRAGMENTED. Contrast her next day:

```
  2026-09-08  meetings=1  longest=7h30  block=09:30 to 17:00  ok
```

One short meeting at the start of the day leaves seven and a half hours clear.
That is a protected day. The two lines side by side are the entire point of the
tool: same person, similar meeting hours over the two days, completely different
attention cost.

## How focus fragmentation is computed

The algorithm is small and the edge cases are where the care goes.

1. Group every occurrence by person and by calendar day.
2. For each person day, take the workday window (09:00 to 17:00 by default).
3. Clip every meeting to that window. A meeting from 08:00 to 09:30 contributes
   only its 09:00 to 09:30 portion. A meeting entirely outside the window
   contributes nothing.
4. Merge overlapping or touching busy intervals so a double booking does not
   count twice and does not create a phantom zero length gap between two
   meetings that abut.
5. Walk from the start of the window across the merged busy intervals, recording
   each gap as a free block, and add the tail from the last meeting to the end
   of the window.
6. The longest free block is the maximum over those gaps.

The edge case that makes this more than a subtraction is overlap and adjacency.
If two meetings overlap, their union is busy, not the sum of their lengths. If
one meeting ends exactly when the next begins, there is no free block between
them even though there are two intervals. Merging first, then walking, handles
both cleanly. Meetings outside the window are dropped rather than clamped to zero
length, so an early morning call does not silently shorten the measured day.

When the data is ambiguous, the tool prefers to under-claim free time rather than
over-claim it. A meeting with a start but no end and no duration is dropped
entirely, because guessing its length could invent free time that does not
exist.

## Reading the focus report

A `FRAGMENTED` line is a prompt, not a verdict. It says this person had no single
stretch on this day long enough for the kind of work you decided needs
protecting. The action depends on why.

If the fragmentation comes from many short meetings, the lever is scheduling:
stack the meetings against one edge of the day so the rest is clear. If it comes
from one or two meetings landing in the middle of the day, the lever is moving
them. If a person is fragmented most days, the meeting load itself is the
problem, and the `load` and `recurring` reports point at what to cut.

The data graphic below shows each person's longest focus block on the sample
fragmented day against the threshold. Ada's bar is the one that falls short.

![Horizontal bar chart of the longest daily focus block per person on
2026-09-07: Ada 90 minutes below the 120 minute threshold, Bao 150 minutes, Chen
180 minutes](docs/assets/focus-fragmentation.svg)

## Recurrence support and its honest limits

meetingtax expands the two recurrence frequencies that cover most standing
meetings, and it refuses to guess at the rest.

Supported and expanded:

- `FREQ=DAILY` with `INTERVAL`, `COUNT`, and `UNTIL`.
- `FREQ=WEEKLY` with `INTERVAL`, `COUNT`, `UNTIL`, and `BYDAY`.

Parsed but not expanded:

- `FREQ=MONTHLY` and `FREQ=YEARLY`. These carry rules such as BYMONTHDAY,
  BYSETPOS, and BYDAY ordinals that are easy to get subtly wrong. Rather than
  produce plausible looking but incorrect dates, the tool counts only the first
  instance and lists the series under recurrence rules not expanded, with the
  frequency named.

When a series has no COUNT and no UNTIL, an expanded rule is bounded to a fixed
horizon so the output stays finite. The bound is a fixed number of steps, not a
wall-clock date, so identical input always produces identical output.

This is a deliberate refusal. A calendar tool that silently mishandles a monthly
rule is worse than one that says plainly which rules it does not expand.

## Exit codes

The exit code lets you wire the tool into a script or a check without parsing its
text.

| Code | Meaning |
| --- | --- |
| 0 | Clean. No findings for this subcommand. |
| 1 | Findings present: a fragmented day, a stale series, or a skipped rule, depending on the subcommand. |
| 2 | Usage error: a missing file, an unreadable calendar, or bad arguments. |

For the sample, `load` exits 1 because one rule was skipped, `focus` exits 1
because one day is fragmented, `recurring` exits 1 because one series is stale,
and `version` exits 0.

## Design decisions

These are the choices that shaped the tool, with the alternative that was
rejected.

Wall-clock time, not converted time zones. A TZID parameter and a trailing Z are
recorded on the parsed value but not applied. The rejected alternative was to
convert every event into one canonical zone. That is correct for a shared
timeline, but wrong for the question the tool asks. Fragmentation is about a
person's own day as they live it, from nine to five in their own chair. Their
09:00 is their 09:00 regardless of what UTC says. Converting would move meetings
across day boundaries and distort exactly the thing being measured. The cost is
that a genuinely cross zone meeting is placed by its literal clock value, which
is stated here as a limitation.

A person instance model, not an event model. Every report works on occurrences,
which are one meeting on one day for one person, rather than on raw events. The
rejected alternative was to keep events whole and special case recurrence and
attendees in each report. Expanding once, up front, means the fragmentation code
never has to think about recurrence at all, and person hours fall out naturally.

Merge then walk, not subtract. Free time could be computed as window length
minus busy length. That was rejected because it gives the total free time, not
the longest single block, and the longest block is the whole point. Walking the
merged intervals gives the blocks themselves.

A round slot heuristic, stated as a heuristic. The could-be-shorter count keys
on meetings longer than 25 minutes whose length is an exact multiple of 30. The
rejected alternative was to claim to know which meetings were too long, which no
tool can do from a calendar alone. The heuristic flags the pattern of booking to
a round slot and names itself a heuristic so nobody mistakes it for a judgment
about a specific meeting.

Refuse unsupported recurrence loudly. The rejected alternative was a best effort
expansion of monthly and yearly rules. Best effort on recurrence is how calendars
end up with meetings on the wrong day. Naming the skipped rule is more useful
than a wrong date.

## Repository layout

```
meetingtax/
  README.md                      this file
  LICENSE                        MIT, holder Zephyr
  CHANGELOG.md                   release notes
  pyproject.toml                 setuptools, src layout, console script
  .gitignore                     ignores build and cache artifacts
  src/meetingtax/
    __init__.py                  package version
    __main__.py                  python -m meetingtax entry point
    cli.py                       argparse subcommands and exit codes
    ics.py                       iCalendar reader: unfold, escape, dates, RRULE
    events.py                    occurrence and recurrence expansion
    fragments.py                 per person per day free block computation
    recurring.py                 stale recurring series analysis
    report.py                    line oriented report formatting
  tests/
    test_ics.py                  parser unit tests
    test_events.py               expansion unit tests
    test_fragments.py            free block unit tests
    test_recurring.py            recurring analysis unit tests
  samples/
    team-calendar.ics            hand authored test vector
    README.md                    how the fixture was built
  docs/assets/
    logo.svg                     wordmark with a day strip mark
    focus-fragmentation.svg      longest focus block per person, real numbers
```

## Glossary

Occurrence. One meeting on one day for one person. The unit every report works
on after expansion.

Workday window. The clock range within which focus is measured, 09:00 to 17:00
by default, adjustable with `--day-start` and `--day-end`.

Free block. A gap inside the workday window with no meeting in it.

Longest free block. The single longest such gap on a given person day. The
measure of how much uninterrupted time was available.

Threshold. The minimum longest free block you declare as enough for real focused
work, in minutes, adjustable with `--threshold`.

Fragmented day. A person day whose longest free block is below the threshold.

Stale series. A recurring meeting this tool expanded that repeats without its
attendee set or duration ever changing.

Person hours. Meeting duration summed across attendees, so a one hour meeting
with three people is three person hours.

## Integration notes

The exit codes make the tool usable as a check. In a scheduled job you might run
`focus` and treat exit 1 as a signal to post the fragmented days to a channel,
while exit 2 means the export itself failed and needs a human.

Because output is line oriented and deterministic, two runs diff cleanly. Save a
report to a file, commit it, and a later run produces a diff that shows exactly
which days changed shape. There is no timestamp or random ordering in the output
to create noise in that diff.

## Verification

Run the test suite from the project root:

```
PYTHONPATH=src python -m unittest discover -s tests -v
```

The suite has 36 tests across four files. They cover line unfolding and its
single whitespace rule, parameter parsing including quoted values, TEXT
unescaping, DATE and DATE-TIME parsing with UTC and TZID variants, DURATION
parsing including a negative duration, RRULE parsing for the supported and
unsupported cases, VEVENT extraction that ignores nested VALARM blocks, duration
used when DTEND is absent, an unclosed VEVENT raising an error, occurrence
expansion for single meetings and for daily and weekly rules, the skipping of
unsupported rules while keeping the first instance, deterministic ordering, free
block computation for empty, single block, scattered, overlapping, and
out-of-window cases, the fragmented day count against a threshold, and stale
series detection.

The SVG assets both parse as XML and contain none of the forbidden filter
elements. The numbers in the focus fragmentation graphic come from the focus
report shown above: Ada 90 minutes, Bao 150 minutes, Chen 180 minutes on
2026-09-07, against a 120 minute threshold.

## Limitations

- Time zones are not converted. A TZID or a trailing Z is recorded but the
  wall-clock value is used. A meeting scheduled across zones is placed by its
  literal clock time, which can be wrong for a genuinely remote attendee.
- Only DAILY and WEEKLY recurrence is expanded. MONTHLY and YEARLY rules are
  counted once and listed as skipped. EXDATE and RDATE are not read, so
  cancellations and one off additions in a recurring series are not reflected.
- Unbounded recurrences are expanded only to a fixed step horizon, so a truly
  endless series is not projected forever.
- The could-be-shorter count is a heuristic based on round slot lengths. It does
  not know whether any particular meeting needed its full time.
- The staleness check treats any expanded repeating series as unchanging,
  because the source carries one attendee set and one duration per series. It
  does not compare separate VEVENTs that share a summary.
- All day events (VALUE=DATE with no time) are parsed but carry no clock span, so
  they do not contribute busy time to the focus calculation.
- The tool reads VEVENT only. VTODO, VJOURNAL, and VFREEBUSY are ignored.

## Roadmap

Planned, without dates.

- Read EXDATE and RDATE so cancellations and additions in a recurring series are
  respected.
- An option to treat back to back meetings as a single busy stretch with no
  recovery gap, versus inserting a configurable recovery buffer around each
  meeting.
- A diff subcommand that compares two runs and reports which person days got more
  or less fragmented.
- Optional time zone conversion for teams that want a shared timeline, kept off
  by default.

## License

MIT. See [LICENSE](LICENSE). Copyright 2026 Zephyr.

<!-- draft note 964 -->
