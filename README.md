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
