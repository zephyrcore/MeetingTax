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
