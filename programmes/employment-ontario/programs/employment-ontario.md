---
id: employment-ontario
title: Employment and Workplace (Ontario)
order: 50
domains: [hr_security, governance, training_competency, records_management,
          health_safety, compliance_audit]
conforms_to: [employment_standards_ontario, ohrc_ontario, aoda_ontario, ohsa_ontario]

tiers:
  - id: essential
    title: Required of every Ontario employer
    rationale: >
      What an employer owes from its first employee, with no size threshold: the
      Employment Standards Act's minimums and the records that prove them, the
      Human Rights Code's equal treatment and duty to accommodate, and the
      Occupational Health and Safety Act's violence and harassment policies,
      programme and investigations. None of these is a maturity question — an
      employer either meets them or is in contravention, and the remedies run
      backwards for years.
  - id: conformant
    title: Administered rather than assumed
    requires: essential
    rationale: >
      The duties that scale with size and are missed because nothing announces
      them: the two written policies required at 25 employees, the accessibility
      obligations that step up at 20 and at 50, hiring rules that changed in
      2024 and 2026, and terminations checked against what was actually owed.
  - id: certifiable
    title: Demonstrable to a regulator
    requires: conformant
    rationale: >
      The organisation can show, rather than assert, that it met its
      obligations: accessibility conformance tested rather than presumed, and
      the compliance report filed from a record that supports every answer on it.

artifacts:
  # ── essential: no employee-count threshold ─────────────────────────────────
  - {id: emp.employment-standards, tier: essential}
  - {id: emp.record-keeping, tier: essential}
  - {id: emp.human-rights, tier: essential}
  - {id: emp.accommodation-requests, tier: essential}
  - {id: emp.accommodation, tier: essential}
  - {id: emp.violence-harassment, tier: essential}
  - {id: emp.workplace-complaints, tier: essential}
  - {id: emp.complaint-investigation, tier: essential}
  # ── conformant: duties that step up with size and with recent amendments ───
  - {id: emp.workplace-policies, tier: conformant}
  - {id: emp.hiring, tier: conformant}
  - {id: emp.termination, tier: conformant}
  - {id: emp.accessibility-policy, tier: conformant}
  - {id: emp.accessibility-training, tier: conformant}
  - {id: emp.accessibility-feedback, tier: conformant}
  # Departures are a security event as well as an HR one, and employment records
  # are records. Placed rather than restated: the verification that access was
  # removed and assets returned belongs to one procedure, not two, and the ESA's
  # retention periods belong in the one retention schedule.
  - {id: isec.policy, tier: conformant}
  - {id: isec.classification, tier: conformant}
  - {id: isec.access-control, tier: conformant}
  - {id: isec.personnel-security, tier: conformant}
  - {id: rec.policy, tier: conformant}
  - {id: rec.retention-schedule, tier: conformant}
  # ── certifiable ────────────────────────────────────────────────────────────
  - {id: emp.accessible-information, tier: certifiable}
  - {id: emp.accessibility-report, tier: certifiable}
---

Four Ontario statutes that every employer in the province is under, and that no
programme in this corpus previously answered.

**The Employment Standards Act, 2000** sets the minimums — wages, hours, rest,
overtime, public holidays, vacation, leaves, notice and severance — and the
records that prove them. It has moved considerably in recent years and the
movement is the part organisations miss: a written policy on disconnecting from
work and a written policy on electronic monitoring, both required of employers
with 25 or more employees and both due before 1 March each year; a prohibition
since 1 July 2024 on knowingly engaging an unlicensed temporary help agency or
recruiter; and, in force 1 January 2026, publicly advertised job postings that
must disclose expected compensation, disclose whether artificial intelligence is
used to screen applicants, state whether the posting is for an existing vacancy,
carry no Canadian experience requirement, and be followed by telling interviewed
applicants the outcome within 45 days.

**The Human Rights Code** has primacy over other Ontario legislation, which is
why it is not one policy among several: a rule that is lawful under the
Employment Standards Act and discriminatory under the Code is unlawful. Its duty
to accommodate has exactly three undue hardship factors — cost, outside sources
of funding, health and safety — and it is procedural as well as substantive, so
delay alone breaches it. That is why the accommodation obligation here is
record-origin, running from the date the request was made.

**The AODA and its Integrated Accessibility Standards Regulation** are the most
prescriptive of the four and the most commonly unmet. Obligations begin at one
employee, step up at 20 (compliance reporting) and again at 50 (written
policies, multi-year plan, WCAG 2.0 Level AA websites), and an organisation that
has grown past a threshold is in breach of several requirements at once with
nothing having told it. The employee count is therefore a column on two
registers here rather than an assumption.

**Workplace violence and harassment sits here, and the placement is a judgement
worth stating.** The Occupational Health and Safety Act's ss. 32.0.1–32.0.8
duties are health and safety law, but the generic `ohs` programme in this corpus
does not carry them — only `construction-ohs-ca` does, written for a constructor
with multiple projects. An office, a clinic, a shop or a plant adopting the
generic occupational health and safety programme would have had no artifact for
the duty at all. `emp.violence-harassment` answers it for a single-workplace
employer, at a different path from the construction one, and an organisation that
has adopted both programmes should remove one from its plan rather than operate
two policies on one duty.

**Two obligations are record-origin**, and both are duties where delay is itself
the breach: an accommodation plan due ten days after the request, and a complaint
investigation due thirty days after the complaint with results to be given to
both parties in writing. Everything else is genuinely periodic.

**One obligation is annual for a filing that is triennial**, and it is declared
that way on purpose. The accessibility compliance report is filed every three
years, the cadence vocabulary has no three-year period, and inventing one would
be worse than being explicit: what recurs every year is the *check* of whether a
report is due and whether the organisation could file a true one — which is the
work that has to happen annually anyway, and the interval is recorded as chosen
because the authority requires the filing rather than the check.

**What is deliberately not here.** Pay equity. The Ontario *Pay Equity Act* binds
private-sector employers with ten or more employees and requires a pay equity
plan to be established and maintained — it is a real and unmet obligation for
most organisations of that size, and it is absent here only because no pay equity
standard exists yet in `standards/` and inventing the control set to cite would
be worse than naming the gap. The Canada Labour Code is also absent, and that one
is correct: it binds federally regulated employers — banks, telecommunications,
interprovincial transport, broadcasting — and an Ontario-incorporated company in
any other line of business is under the Employment Standards Act instead.
Adopting both would produce two contradictory answers to every question about
hours and termination.
