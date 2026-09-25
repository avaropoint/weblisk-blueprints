---
id: emp.hiring
kind: procedure
title: Hiring and Job Postings
structure: procedure
path: procedures/hiring-and-job-postings.md

satisfies:
  - employment_standards_ontario:8.4
  - employment_standards_ontario:74.1.1
  - ohrc_ontario:23
  - aoda_ontario:22
  - aoda_ontario:23
  - aoda_ontario:24
  - iso_27001:A.6.1

requires: [emp.employment-standards, emp.human-rights]

declares:
  obligation:
    id: emp.posting-review
    activity: Review job postings and hiring records against the posting, human rights and accessibility requirements
    cadence: each quarter
    authority: ESA Part III.1 — publicly advertised job posting requirements, in force 1 January 2026
    interval_basis: chosen
    responsible: hr-lead
    applies_to: the organisation
    records: registers/job-posting-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Job Posting Review Record
    note: >
      One row per review. The columns are the specific requirements rather than
      a single compliance flag, because each of them is a separate contravention
      and an organisation that meets four of five needs to know which one it
      missed.
    layout: form
    review: required
    approvers: [hr-lead]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: postings, label: Publicly advertised postings in the period, type: int, required: true}
      - {key: compensation_disclosed, label: With expected compensation or range, type: int, required: true}
      - {key: ai_use_disclosed, label: Disclosing whether AI is used to screen, type: int, required: true}
      - {key: vacancy_status_stated, label: Stating whether the posting is for an existing vacancy, type: int, required: true}
      - {key: canadian_experience, label: Containing a Canadian experience requirement, type: int, required: true}
      - {key: accommodation_notice, label: Stating that accommodation is available, type: int, required: true}
      - {key: interviewed, label: Applicants interviewed, type: int, required: true}
      - {key: outcome_within_45_days, label: Informed of the outcome within 45 days, type: int, required: true}
      - {key: postings_retained, label: Postings and applications retained three years, type: bool, required: true}
      - {key: agencies_licensed, label: Agencies and recruiters used were licensed, type: bool, required: true}
      - {key: actions, label: Actions taken, type: longtext, required: true}
---

What this document must establish for THIS organisation: what goes in a job
posting, what may be asked of an applicant, and what happens to the people who
were not hired.

It must carry the posting requirements that came into force on 1 January 2026
for publicly advertised postings: expected compensation or a range, disclosure of
whether artificial intelligence is used to screen, assess or select applicants,
a statement of whether the posting is for an existing vacancy, and no Canadian
experience requirement in the posting or in the application form. An applicant
who is interviewed must be told whether a hiring decision was made, within 45
days of the last interview, and the posting and its application forms must be
kept for three years after public access to the posting ends.

It must state what may not be asked, which is the Human Rights Code's ground.
Questions about citizenship, age, marital or family status, place of origin,
creed, disability or record of offences are prohibited in advertisements,
application forms and interviews unless the ground is a reasonable and bona fide
qualification. Questions about the ability to meet the essential duties, with or
without accommodation, are permitted — and that distinction is the whole of the
training an interviewer needs.

It must include the accessibility duties, which apply from the first posting.
Notify the public and employees that accommodation is available for applicants
with disabilities; notify an applicant selected for assessment that
accommodations are available on request and consult with them if asked; and tell
a successful applicant about the organisation's accommodation policies when
making the offer.

It must say what happens before an agency or recruiter is engaged. Since 1 July
2024 it is a contravention for an employer to knowingly use an unlicensed
temporary help agency or recruiter, licences are published in a searchable public
registry, and the obligation is continuous rather than a one-time check.

It must cover screening proportionately and lawfully. A criminal record check
demanded for every role is both an excessive collection of personal information
and a Human Rights Code problem, because record of offences is a protected ground
— screening has to be tied to what the role actually requires, which is the same
test the security programme's personnel screening applies.
