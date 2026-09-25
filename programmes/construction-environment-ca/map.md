---
id: construction_environment_ca
title: Construction Environmental Protection Programme (Canada — Ontario)
order: 21
domains:
  - environmental
  - trade_regulatory
  - incident_response
  - records_management
  - compliance_audit
  - risk_management
conforms_to:
  - o_reg_406_19
  - epa_ontario
  - owra_ontario

tiers:
  - id: statutory
    title: Lawful to dig, and lawful to move what comes out
    rationale: >
      What an Ontario contractor that excavates must have in place before a
      bucket goes in the ground. Every artifact at this line answers a
      prohibition rather than a preference: soil may not leave a project area
      before a notice is filed where one is owed; a contaminant may not be
      discharged where it causes or may cause an adverse effect; water may not be
      taken above fifty thousand litres a day, nor sewage works operated, nor a
      contaminant discharged to air or land, except under an instrument. Below
      this line the organisation is not unaudited, it is committing offences
      under two statutes, and the consequence does not arrive as a finding at a
      review: it arrives as a provincial officer's order stopping the excavation,
      and as a charge that names the corporation and the person who directed it.
      Several artifacts here are conditional on the work being done at all. None
      of them is conditional on the organisation being ready.
  - id: defensible
    title: It can still be shown three years later
    requires: statutory
    rationale: >
      This tier is deliberately small, and the smallness is the finding. Almost
      everything in Ontario environmental law for a contractor is a prohibition
      with a record attached, so there is very little that is merely good
      practice — which is why the statutory tier is fifteen artifacts and this
      one is three. What is here is the work of looking: an instrument's
      conditions read against what the site is actually doing, an expiry acted on
      before it passes, and somebody reading the whole programme at once on a
      cycle. None of it is required by any instrument. All of it is what turns a
      set of records into an answer, and the question it answers is the one asked
      in a prosecution and in a purchaser's due diligence alike — not "did you
      have a permit" but "what were you doing about it".

# ── the standing work adopting this programme takes on ──────────────────────
#
# An environmental programme that is not running is a folder of determinations
# nobody made and a Registry notice nobody closed. These four are the things
# that must actually happen: somebody is told what is due before the trucks
# are loaded, the instruments that authorise the work are looked at before they
# lapse, an incident is not allowed to sit undecided overnight, and the shape of
# the whole thing is measured on a cycle rather than at an inspection.
#
# Every one is created PAUSED. Turning them on is one switch each, and the
# switch is the organisation's.
operations:
  - id: due-sweep
    title: What is due
    does: due-sweep
    schedule: {cadence: daily, at: "05:45"}
    why: >
      A Registry notice is owed before soil leaves the project area, and soil
      leaves early. A list of what is due today is of use only to somebody who
      can still act on it, so this runs before loading starts rather than at the
      start of an office day. It reports and never remediates.

  - id: instrument-watch
    title: Approvals, registrations and permits
    agent: >
      Report on the instruments that authorise what this organisation is doing to
      air, land and water.

      Read registers/environmental-approvals.md, registers/approval-renewals.md,
      registers/approval-condition-checks.md and
      registers/dewatering-operations.md. For every instrument report what it
      authorises, who holds it, the date it expires and whether a renewal has
      been applied for. For every dewatering operation whose status is operating,
      report the instrument it is running under and whether that instrument is in
      force.

      Separate four states and never merge them. EXPIRED — the instrument has
      passed its date and the activity should have stopped. EXPIRING — it falls
      due inside ninety days and somebody has to act now. UNAUTHORISED — an
      activity is running and no row names an instrument for it, which is the
      most serious thing you can find and belongs first in the report. UNKNOWN —
      the register has no row, or the row has no date, which is not the same as
      in force and must never be reported as such.

      Say plainly where a register could not be read. A check that could not
      parse its source has refuted nothing, and an empty result reported as a
      clean one is worse than no report.

      Do not write any file, do not create any document request, and do not
      contact anybody: this is a report to the people who can.
    needs: [read]
    schedule: {cadence: weekly, at: "07:00", weekday: monday}
    why: >
      An expiry is the one clock in this programme that no activity generates:
      an instrument lapses whether or not anybody worked that week. On a Monday,
      because the question is what we are lawfully able to do this week.

  - id: open-incident-watch
    title: Incidents, observations, and soil that has not been closed out
    agent: >
      Report on everything in this programme that is open.

      Read registers/environmental-incidents.md, registers/spill-reports.md,
      registers/soil-contamination-observations.md,
      registers/soil-contamination-assessments.md,
      registers/excavation-projects.md and
      registers/excess-soil-registry-updates.md.

      Answer four questions, in this order. Is there an environmental incident
      with no reportability decision recorded against it — a duty owed forthwith
      with nobody yet deciding whether it applies? Is there an observation
      suggesting soil contamination whose status is open, and has excavation
      resumed on it? Is there a project area whose last load left more than
      thirty days ago with no Registry close-out recorded? And is there any
      incident where the record says notification was not made forthwith?

      Name the first and the last of those plainly and first. They are not
      paperwork findings: one is a duty running now with nobody on it, and the
      other is a contravention this organisation has already written down.

      Report separately anything whose status field is blank. A blank status has
      not been decided about, and it is not closed by default.

      Do not write any file and do not contact anybody. State what could not be
      read rather than passing over it.
    needs: [read]
    on: [obligation.overdue]
    schedule: {cadence: daily, at: "16:30"}
    why: >
      Two clocks on purpose. The event catches a reporting deadline going past
      on the day it happens; the afternoon sweep catches the day on which
      nothing fired because the server was down, and runs late enough to see
      what the day's work found. This is the one report in the programme where
      the answer can be that a duty owed forthwith is running and nobody has
      picked it up.

  - id: programme-readiness
    title: Programme readiness
    does: programme-readiness
    schedule: {cadence: monthly, at: "07:30", day: 1}
    why: >
      Both numbers on a cycle: how much of the programme exists as current,
      cited documents, and how much of it is producing attested records. Monthly
      rather than weekly because a programme does not move week to week. It
      reports; it never drafts what it finds missing.

artifacts:
  # ── statutory: lawful to dig, and lawful to move what comes out ────────────
  - { id: cenv.policy, tier: statutory }
  - { id: cenv.excavation-projects, tier: statutory }
  - { id: cenv.soil-reuse-planning, tier: statutory }
  - { id: cenv.excess-soil-registry, tier: statutory }
  - { id: cenv.registry-closeout, tier: statutory }
  - { id: cenv.soil-destinations, tier: statutory }
  - { id: cenv.soil-hauling, tier: statutory }
  - { id: cenv.soil-observations, tier: statutory }
  - { id: cenv.contaminated-soil-response, tier: statutory }
  - { id: cenv.environmental-incidents, tier: statutory }
  - { id: cenv.spill-reporting, tier: statutory }
  - { id: cenv.environmental-approvals, tier: statutory }
  - { id: cenv.approvals-determination, tier: statutory }
  - { id: cenv.dewatering-operations, tier: statutory }
  - { id: cenv.dewatering, tier: statutory }
  # ── defensible: it can still be shown three years later ────────────────────
  - { id: cenv.approval-conditions, tier: defensible }
  - { id: cenv.approval-renewal, tier: defensible }
  - { id: cenv.compliance-review, tier: defensible }
---

Eighteen artifacts for an Ontario general contractor that excavates — which is
to say, for almost any general contractor, because the duties below are triggered
by digging a hole and taking what comes out of it somewhere else.

## Who this programme is for

**The line is excavation with removal.** A contractor that excavates and puts the
soil back in the same project area is outside most of O. Reg. 406/19, because
what the regulation governs is *excess* soil — soil excavated as part of a
project and removed from the project area. A contractor that takes soil off site
is inside it, whatever the volume, because two of its duties have no threshold at
all. A contractor that does no excavation whatever still needs the spill half of
this programme, because a fuel spill in a compound is a spill wherever it
happens.

A company that does not excavate, does not dewater, and holds no environmental
instrument should **not** adopt the whole of this programme. Adopting a programme
that does not apply does not produce a cautious organisation; it produces
obligations that will never be discharged, gaps that can never be closed, and a
readiness number nobody believes. Such a company should take the policy, the
environmental incident register and the spill reporting procedure, and leave the
soil and approvals artifacts alone.

## The two duties that are owed on every job, whatever the volume

This is the sentence that decides whether an organisation gets this area right,
and it is the opposite of what most contractors are told.

The Excess Soil Registry regime in s. 8 is **triggered, and mostly does not
apply.** A notice is owed only where the project area meets one of three criteria
in subsection 8 (1.1), and Schedule 2 then removes seven further sets of
circumstances on top of that. On a large majority of ordinary jobs, no notice is
owed and no qualified person is needed.

Two duties do not care about any of that:

- **The hauling record (s. 18).** A record travels with every load, created and
  confirmed as accurate by the owner or operator of the site where the soil is
  loaded *before the load leaves*, and completed on arrival with the receiving
  contact's acknowledgement. The only exceptions are 5 m³ or less of dry excess
  soil and soil packaged as a landscaping product — and even then the information
  goes to a provincial officer on request.
- **The written procedure for an observation suggesting contamination (s. 23).**
  Owed by the project leader **or** the operator of the project area, on every
  project area, requiring all excavation to cease immediately, the project leader
  to be notified immediately, and the affected soil to be identified and
  segregated before work resumes.

An organisation that reads "no Registry notice is owed" as "no excess soil
paperwork is owed" has the regulation exactly backwards, and it is the commonest
and most expensive error in this area. `cenv.soil-hauling` and
`cenv.contaminated-soil-response` are both in the statutory tier for that reason,
with no dependency on a notice ever having been filed.

## Why a determination is recorded on every project area, and a filing on few

The heart of this programme is not the filing. It is
`registers/excavation-projects.md`, where every project area gets a row and every
row gets an answer to two questions: **are we the project leader here**, and **is
a notice owed**.

The criteria are not a rule anybody carries in their head correctly. A notice is
owed where the project area is or has ever been, in whole or in part, an
**enhanced investigation project area**; or where any part of it is in an **area
of settlement** and **2,000 m³ or more** will be removed, *unless* the whole
project area is in residential, institutional, parkland or agricultural-and-other
use; or where the excavation is a **remediation**. The settlement-area exclusion
is routinely read backwards, and the consequence is precise: a commercial,
community or industrial project area in a settlement area is caught at 2,000 m³
and a residential one is not, and a project area of mixed use is caught, because
the whole of it is not one of the four.

So the honest shape of this obligation is **a determination recorded for every
project area and a filing on the minority of them.** A programme that made every
load a Registry filing would be wrong, would cost the organisation money it does
not owe, and would be abandoned inside a month — and the abandonment would take
the filings that *were* owed with it.

`registry_notice_required` therefore has four negative answers rather than one:
no criterion was met, a criterion was met and Schedule 2 exempted it, we are not
the project leader, or not yet determined. Collapsing them loses the only
information that could ever show the determination was made properly.

## The exemption that ended on 1 January 2026

Until that date, clause 8 (2) (b) exempted a project where the project leader had
entered into a contract with another person for the management of excess soil
from the project **before 1 January 2022**. That clause was revoked when the
final tranche of the phase-in commenced on **1 January 2026**. Any long-running
job that was relying on it is inside the Registry regime now, and the first place
it shows up is a project area whose row has never had a notice and whose soil is
still moving. An organisation that learned this regulation during the phase-in
learned a rule that no longer exists, and this programme says so in the artifact
rather than assuming somebody read the amendment.

## Project leader, operator, and the assumption that costs the most

The reuse planning and Registry duties in ss. 8 to 16 run against the **project
leader** — the person or persons ultimately responsible for making decisions
relating to the planning and implementation of the project. On a stipulated-price
job for a municipality that is usually the owner; on a design-build or a
self-performed development it is usually this organisation, and on a construction
management contract it is a question with a real answer that somebody has to give.

It cannot be decided once for all projects, and the organisation that assumes it
is never the project leader discovers that it was one when a notice was never
filed. So `our_role` is a required column with "Not yet determined" as a state,
and the policy requires the question to be answered per project area rather than
answering it.

And "we are not the project leader" is never the end of the work. The s. 23
procedure is owed by the project leader **or** the operator of the project area;
the s. 18 hauling record is owed by the owner or operator of the site where the
soil is loaded. On a job where somebody else is the project leader, this
organisation is very often the operator, and both of those are still ours.

## Forthwith, and why this programme will not pretend to express it

The reporting duties here are the only ones in this corpus with no period at all.
A spill is notified **forthwith**, the duty taking effect the moment the person
knows or ought to know. The duty to do everything practicable to prevent,
eliminate and ameliorate the adverse effect and to restore the natural
environment is owed on the same footing, independently of whether anybody was
notified.

The platform's deadline vocabulary cannot say "forthwith", and a deadline that
pretended to would be a worse lie than an honest one. So `cenv.spill-reporting`
is declared with a twenty-four hour deadline that is explicitly **the deadline
for the record of the call, not for the call**, marked `interval_basis: chosen`,
with the statutory word stated in the authority — and its register asks
`reported_forthwith` as a separate required question, so that a late call cannot
hide behind a punctual form.

## Three kinds of clock, and never blended

Every obligation here declares `interval_basis`, because this area mixes
instruments that set a period with instruments that set none:

- **`required`** — the interval is the regulation's. There are exactly two: the
  Registry close-out, which is thirty days after the last load under s. 9 (2),
  and the review and amendment of a qualified person's documents, which is thirty
  days from the circumstance becoming known under s. 15 (2).
- **`chosen`** — the instrument requires the activity or prohibits the outcome
  and sets no interval. The thirty days for reuse planning, the five days for the
  notice, the sixty days for an approval determination, the ninety days for a
  renewal, the monthly hauling reconciliation, the quarterly condition check, the
  weekly discharge check and the quarterly review: every one of those numbers is
  this organisation's, and each artifact says so in words.

And one case the schema cannot express, which the prose therefore must: where an
**instrument sets its own frequency** — daily volumes under O. Reg. 63/16, a
sampling regime in a permit, limits in a sewer-use by-law — that frequency
governs, and the `chosen` weekly or quarterly check above confirms that it
happened rather than replacing it. `interval_basis: chosen` on
`cenv.dewatering` means "the week is ours". It never means the instrument's
frequency is optional.

## Per project area, per instrument, per discharge — in the data

Almost nothing here happens once for the company. A hauling reconciliation is one
per project area per month; a condition check is one per instrument per quarter;
a discharge check is one per dewatering operation per week. `applies_to` has no
vocabulary for any of those, deliberately, and writing `each project` would mean
one discharge check a week for an organisation running four dewatering
operations — one of them discharging the obligation for all four, and the
programme reporting a hundred per cent while three ran unchecked.

So the expansion happens in the data. `registers/excavation-projects.md`,
`registers/environmental-approvals.md` and `registers/dewatering-operations.md`
are standing registers whose rows are the subjects, each with the pair of dates
that says when a subject enters and leaves, and every recording register carries
a relation column back onto its subject.

Which makes the **dewatering register's grain load-bearing**. It holds one row
per dewatering *operation*, not per site: an excavation running a winter sump and
a summer wellpoint array is two discharges with two rates and two receiving
bodies, and a register that merged them would expect one check between them.

## The record-origin chains

Five obligations are triggered by rows rather than by a calendar, because the
work has no period — a project area is excavated once, an observation is made at
a moment, an instrument expires on a date:

    excavation projects → reuse planning,        30 days before excavation starts
    excavation projects → the Registry notice,    5 days before excavation starts
    excavation projects → the approval determination, 60 days before it starts
    excavation projects → the Registry close-out, 30 days after the last load
    soil observations   → the qualified person's review, 30 days after the observation
    environmental incidents → the reporting record, 24 hours after discovery
    approvals           → renewal, 90 days before the instrument expires

Every one writes into a register other than the one that triggered it. A trigger
whose recording register is its own trigger register discharges every occurrence
at the moment it creates one, reporting completeness having checked nothing.

And every chain terminates in `cenv.compliance-review`'s quarterly sweep, which
exists for a reason worth stating plainly: **a row that was never created
triggers nothing.** A project area nobody wrote down raises no determination, no
filing and no close-out. It is not late, it is absent, and the due list is silent
about it. The review is the one artifact that asks what is missing rather than
what is overdue.

## What is deliberately not here

**Designated substances, asbestos and worker exposure.** These are duties under
the *Occupational Health and Safety Act* and its regulations, they run against
the employer and the constructor rather than the project leader, and they are
answered in full by the construction health and safety programme —
`cohs.designated-substances` and `cohs.asbestos-management`. They are not
repeated here, and the join matters: the contaminated material a designated
substances survey found becomes an environmental obligation the moment it is
loaded into a truck, and neither programme may assume the other has it.

**Excavation support, trench safety and the notice of project.** Also the health
and safety programme's — `cohs.excavation-trenching` and
`cohs.notice-of-project`. This programme is about what comes out of the hole, not
about the hole being safe to stand in.

**Species at risk, archaeological resources, and the federal fisheries regime.**
The *Endangered Species Act, 2007*, the *Ontario Heritage Act* and the federal
*Fisheries Act* all bind work in the ground, all have their own regulator and
their own trigger, and none of them is here. They are genuinely absent rather
than out of scope. A contractor working in or near water, or on land with known
archaeological potential, has duties this programme will not find.

**Waste other than soil.** Construction and demolition waste, the generator
registration regime, hazardous waste manifesting and the waste audit and
reduction work plan requirements under O. Reg. 102/94 and O. Reg. 103/94 are a
programme of their own, with a different register and a different duty-holder.
Excess soil left this regime when O. Reg. 406/19 was made, and the rest of the
skip did not.

**Air, noise and dust as a nuisance.** Section 14's reach into dust, odour, noise
and vibration is stated in the policy and in the incident register's categories,
but the operative limits on a construction site are usually a municipal by-law's
and a contract specification's. Those are not provincial instruments and this
corpus does not carry them.

**Climate, sustainability and embodied carbon reporting.** Not a legal duty for
an Ontario contractor, increasingly a tender requirement, and a programme that
shipped one as though it were the former would assert a legal basis that does not
exist.

**Anything the research could not verify.** No section number, threshold, volume
or date appears here that could not be read from the instrument. Where the law is
silent about an interval, the artifact says the law is silent and the number is
marked as this organisation's.
