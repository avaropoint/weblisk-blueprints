---
id: cohs.daily-crew-assignments
kind: register
title: Register of Daily Crew Assignments
structure: standard
path: registers/construction/daily-crew-assignments.md

# A register carries no `satisfies:`.
#
# It is the evidence that work happened, not the document that answers a
# control — and the relation vocabulary says so structurally: `implements`
# onto a control may be asserted by a blueprint, a policy or a procedure,
# and by nothing else. A register citing a control could never be recorded
# as answering it, so it sat at `present_uncited` permanently and capped the
# tier's readiness at a number no amount of work could move.
#
# The citation belongs on the procedure that declares this register, which
# is where the organisation states what it does; this file is where it
# records having done it.

requires: [cohs.project-register]

register:
  title: Register of Daily Crew Assignments
  note: >
    One row per crew per working day: which crew, on which project, doing what,
    under whom. It is deliberately thin — it is not a timesheet and not a
    production record. Its job is to say how many pre-task hazard assessments
    ought to exist today, which is a question nothing else in the programme can
    answer.
  columns:
    - {key: assignment_id, label: Assignment, type: text, required: true}
    - {key: work_date, label: Date, type: date, required: true}
    - {key: project, label: Project, type: relation, required: true,
       target: /registers/construction/projects.md#records, display: project_id}
    - {key: crew, label: Crew, type: text, required: true}
    - {key: trade, label: Trade or discipline, type: text, required: true}
    - {key: supervisor, label: Supervisor, type: user, required: true}
    - {key: headcount, label: Workers, type: int, required: true}
    - {key: work_planned, label: Work planned, type: longtext, required: true}
    - {key: work_area, label: Work area, type: text}
---

What this artifact must establish: which crews are working where, on what day,
under which supervisor.

It exists for one structural reason. A pre-task hazard assessment happens once
per crew per shift, and the platform has no scope called a crew — an occurrence
is expected for the organisation or for a project, and nothing else. Declaring
the assessment "per project" would expect one record a day from a site running
four crews: one crew files, the occurrence is discharged, and the programme
reports complete while three crews' worth of the most important safety
conversation on a construction site is invisible. That is not a gap; it is a
false clean bill.

So the expansion happens here, in the data, where it belongs. One row per crew
per day, and the assessment obligation triggers off these rows — one occurrence
each, due against that row's own date. Four crews produce four expected
assessments and three missing ones are three findings with names attached.

`assignment_id` must be stable and must not be a row number. Rows renumber; a
signature over a record that cites row 14 still verifies while pointing at
somebody else's crew. A composite of the date, the project and the crew is
sufficient and is legible to a person reading a register six months later.

It must be filled in **before** the shift, not reconstructed after it. A register
written at the end of the day to match the assessments received cannot produce a
missing one, which is the only thing it was built to do. The document should say
who enters the rows and when, and should treat a day with no rows on a live
project as a finding rather than as a quiet day.

It is not the crew list. Who was on the crew belongs to the assessment record
itself, signed by the people who were there. What belongs here is the fact that a
crew was assigned, which is what makes an absent assessment visible.
