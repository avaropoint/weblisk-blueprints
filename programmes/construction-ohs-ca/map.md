---
id: construction_ohs_ca
title: Construction Occupational Health and Safety Programme (Canada — Ontario)
order: 20
domains:
  - health_safety
  - training_competency
  - incident_response
  - trade_regulatory
  - equipment_integrity
  - records_management
conforms_to:
  - ohsa_ontario
  - o_reg_213_91
  - o_reg_297_13
  - o_reg_632_05
  - o_reg_278_05
  - o_reg_559_22
  - skilled_trades_ontario
  - reg_860_whmis
  - wsia_ontario
  - reg_1101_first_aid
  - cor_2020
  - iso_45001
  - isnetworld
  - csa_z462

tiers:
  - id: essential
    title: Legally required
    rationale: >
      What a constructor or an employer must have in place to put workers on an
      Ontario construction project lawfully. This tier is large, and it is large
      because the law is: construction is the most heavily prescribed workplace
      in the province, and a tier drawn to look like a comfortable first step
      would have to leave out fall protection, confined space entry, excavation
      support or the notice of project — each of which is a duty on the day work
      starts, not an aspiration. Below this line the organisation is exposed, not
      merely unaccredited. Several artifacts here are conditional on the work
      being done at all; none of them is conditional on the organisation being
      ready for it.
  - id: conformant
    title: Audit-ready
    requires: essential
    rationale: >
      The programme can be shown to work to somebody who was not there. What
      each position must hold is written down and joins to what people actually
      hold; the instruments that bind the organisation are tracked with the
      consolidation date they were last read at; sub-trades are qualified before
      they are engaged rather than after they are on site; and somebody senior
      reviews the whole of it on a cycle. Nothing here is required by the
      Occupational Health and Safety Act. All of it is required by an auditor,
      a prequalification service, or the first serious claim.
  - id: certifiable
    title: Externally auditable
    requires: conformant
    rationale: >
      The programme audits itself on the cycle the certifying body actually
      runs, and produces the numbers an owner asks for without a scramble.
      Worth stating plainly, because the two cycles in this industry are
      routinely transplanted onto one another: an accredited ISO 45001
      certificate requires an external audit from the certification body in
      EVERY calendar year, whereas COR 2020 is external in year one and internal
      maintenance in years two and three. An organisation that budgets the COR
      cycle against an ISO certificate loses the certificate.

# ── the standing work adopting this programme takes on ──────────────────────
#
# Documents alone are a binder. These are the four things that must be RUNNING
# for the programme above to be a programme: somebody is told what is due,
# somebody senior hears when that is ignored, the instruments that let a
# sub-trade on site are checked before they lapse, and the whole of it is
# measured on a cycle rather than at audit.
#
# Every one of them is created PAUSED. A schedule sends people work unattended,
# and adopting a programme must not start doing that on a cadence this
# organisation did not choose. Turning them on is one switch each, and the
# switch is the organisation's.
operations:
  - id: due-sweep
    title: What is due
    does: due-sweep
    schedule: {cadence: daily, at: "06:00"}
    why: >
      Construction work is dispatched before seven. A report about what is due
      today is only of use to the person who can still do something about it,
      so this runs before the crews are assigned rather than at the start of an
      office day. It reports every obligation in the project — the daily hazard
      assessments, the weekly site inspections, the credentials inside their
      renewal window — and tells the position each one belongs to, once, when
      it advances. It never remediates.

  - id: escalation-review
    title: Escalated work, and whether escalation is working
    agent: >
      Report on the health-and-safety work that has escalated in this project.
      Use the governance and search tools to read the obligation registers and
      the current due list. For each occurrence that has passed its declared
      grace and become another position's problem, say what the activity was,
      which position it belonged to, which position it escalated to, and how
      many days late it is now.

      Then answer the question the counts alone do not: is escalation being
      used here as a safety net, or as the normal path? An escalation that
      fires as a matter of routine is a finding about the declaration — either
      the grace is shorter than the work takes, or the position it lands on is
      not the one that can act — and it is worth saying that it is one or the
      other even when the records cannot say which.

      State both readings and prefer neither. Never recommend lengthening a
      cadence or a grace period in order to make the numbers improve. Do not
      write any file, do not create any document request, and do not contact
      anybody: your whole output is this report.
    needs: [read]
    on: [obligation.escalated]
    schedule: {cadence: weekly, at: "07:00", weekday: monday}
    why: >
      Two clocks on purpose. The trigger catches an escalation on the day it
      happens; the Monday sweep catches the week in which nothing escalated
      because the server was down, and is the only view that can see whether
      escalation has quietly become the route by which work gets done.

  - id: sub-trade-currency
    title: Sub-trade clearance and certificate currency
    agent: >
      Check whether every sub-trade currently engaged on this project is
      covered by the instruments that let them be on site.

      Read registers/clearance-certificates.md, registers/statutory-credentials.md
      and registers/subcontractor-requalifications.md, plus the procedures that
      govern them. For each sub-trade, report: the clearance certificate held
      and the date it was valid to; whether the insurance certificates recorded
      at requalification are still current; whether the requalification itself
      is inside its own interval; and which statutory credentials held by that
      sub-trade's people expire inside the next ninety days.

      Separate three things that a single list would blur: LAPSED — the
      instrument has expired and the work should not be proceeding; EXPIRING —
      it is inside the notice period and somebody has to act now; and UNKNOWN —
      the register has no row, or the row has no date, which is not the same as
      compliant and must never be reported as such.

      Say plainly when a register could not be read. A check that could not
      parse its source has refuted nothing, and reporting an empty result as a
      clean one is worse than reporting nothing at all.

      Do not write any file, do not create any document request, and do not
      contact any sub-trade: this is a report to the people who can.
    needs: [read]
    schedule: {cadence: weekly, at: "07:30", weekday: monday}
    why: >
      A clearance certificate is the one document whose lapse transfers
      liability for a sub-trade's workers onto the constructor, and it is
      issued with a validity date rather than a fixed term — so it cannot be
      derived from a cadence and has to be looked at. Weekly, and on the same
      morning as the escalation review, because both are the constructor's
      Monday question: who is on our sites this week, and are they allowed to
      be.

  - id: programme-readiness
    title: Programme readiness
    does: programme-readiness
    schedule: {cadence: monthly, at: "07:00", day: 1}
    why: >
      Both readiness numbers on a cycle: how much of the programme exists as
      current, cited documents, and how much of it is producing attested
      records. Monthly rather than weekly because a programme does not move
      week to week, and a report that says the same thing four times a month is
      one nobody reads by the second. It reports; it never drafts the documents
      it finds missing.

artifacts:
  # ── essential: lawful to put a worker on a project ─────────────────────────
  - { id: cohs.policy, tier: essential }
  - { id: cohs.project-register, tier: essential }
  - { id: cohs.constructor-duties, tier: essential }
  - { id: cohs.notice-of-project, tier: essential }
  - { id: cohs.site-orientation, tier: essential }
  - { id: cohs.jhsc, tier: essential }
  - { id: cohs.site-inspections, tier: essential }
  - { id: cohs.equipment-inspections, tier: essential }
  - { id: cohs.daily-crew-assignments, tier: essential }
  - { id: cohs.pre-task-hazard-assessment, tier: essential }
  - { id: cohs.ppe, tier: essential }
  - { id: cohs.fall-protection-equipment, tier: essential }
  - { id: cohs.fall-protection, tier: essential }
  - { id: cohs.credential-register, tier: essential }
  - { id: cohs.credential-renewal, tier: essential }
  - { id: cohs.working-at-heights-training, tier: essential }
  - { id: cohs.whmis, tier: essential }
  - { id: cohs.confined-space, tier: essential }
  - { id: cohs.confined-space-entry-permits, tier: essential }
  - { id: cohs.excavation-trenching, tier: essential }
  - { id: cohs.traffic-protection, tier: essential }
  - { id: cohs.electrical-safety, tier: essential }
  - { id: cohs.hoisting-rigging, tier: essential }
  - { id: cohs.suspended-access, tier: essential }
  - { id: cohs.elevating-work-platforms, tier: essential }
  - { id: cohs.designated-substances, tier: essential }
  - { id: cohs.asbestos-management, tier: essential }
  - { id: cohs.violence-harassment, tier: essential }
  - { id: cohs.work-refusal, tier: essential }
  - { id: cohs.work-refusals, tier: essential }
  - { id: cohs.fire-protection, tier: essential }
  - { id: cohs.trade-certification, tier: essential }
  - { id: cohs.incident-reporting, tier: essential }
  - { id: cohs.incidents, tier: essential }
  - { id: cohs.incident-investigation, tier: essential }
  - { id: cohs.corrective-actions, tier: essential }
  - { id: cohs.notifiable-events, tier: essential }
  - { id: cohs.injury-notices, tier: essential }
  - { id: cohs.first-aid-stations, tier: essential }
  - { id: cohs.defibrillator, tier: essential }
  - { id: cohs.site-emergency-response, tier: essential }
  - { id: cohs.wsib-account, tier: essential }
  - { id: cohs.clearance-certificates, tier: essential }
  - { id: cohs.clearance-renewal, tier: essential }
  # ── conformant: it can be shown to work ────────────────────────────────────
  - { id: cohs.competency-requirements, tier: conformant }
  - { id: cohs.regulatory-currency, tier: conformant }
  - { id: cohs.subcontractor-prequalification, tier: conformant }
  - { id: cohs.hot-work-permits, tier: conformant }
  - { id: cohs.return-to-work, tier: conformant }
  - { id: cohs.management-review, tier: conformant }
  # ── certifiable: it audits itself and produces what is asked for ───────────
  - { id: cohs.ohsms-audit, tier: certifiable }
  - { id: cohs.safety-statistics, tier: certifiable }
---

Fifty-two artifacts for a constructor or employer working on construction
projects in Canada, drawn against Ontario law because occupational health and
safety is provincial and Ontario is where the prescription is heaviest. An
organisation working in another province keeps the shape and re-points the
citations: the duties are recognisably the same, the numbers are not.

It is a sibling of the generic occupational health and safety programme rather
than an extension of it. A construction project is not a workplace with extra
hazards bolted on — it has a different duty-holder at the top of it. The
**constructor** is answerable for every employer and every worker on the
project, not only for its own, and almost everything below follows from that
one fact.

## Why the first tier is so large

Forty-four of the fifty-two artifacts sit at `essential`, and that is the
honest count rather than a discouraging one. Ontario prescribes construction in
detail: guardrails at 2.4 m, soil classified to the highest of the types
present, a written traffic protection plan kept at the project, a separate entry
permit for every confined space entry, a defibrillator on any project of twenty
or more workers expected to last three months. Each of those is a duty on the
day work starts. A first tier drawn to be reassuring would have had to omit fall
protection — the leading cause of construction death — and a roadmap that omits
the leading cause of death is not a roadmap.

What the tier does NOT mean is that all thirty-six apply to every organisation.
Suspended access, confined space, excavation and elevating work platforms are
conditional on doing that work at all. They are conditional on the WORK, never
on the organisation's readiness, which is why they are not deferred to a later
tier: the day the first trench is opened is not the day to start writing an
excavation procedure.

## The three kinds of clock, and why they are never blended

The single most damaging thing a compliance product can do in this domain is
state a chosen interval as a legal one. Ontario construction has only about
eleven legally-set recurring clocks; most of what circulates as an "expiry" is a
training provider's card policy or industry convention.

So every obligation here declares `interval_basis`, and it is one of two words:

- **`required`** — the cited authority sets this interval. Working at Heights is
  valid for three years because O. Reg. 297/13 s. 8(1) says so. A joint health
  and safety committee meets at least once every three months because OHSA
  s. 9(33) says so. A defibrillator is inspected quarterly because O. Reg. 213/91
  s. 27.1(7) says so.
- **`chosen`** — the authority requires the activity and sets no interval, and
  the organisation picked one. Excavation inspection, traffic protection plan
  review, the confined space programme review, the monthly verification of
  heights training: all of these are duties in law with no clock in law. The
  number beside them is a policy decision and each artifact's brief says so in
  words.

There is a third case the schema cannot yet express and the prose therefore
must: a duty triggered by an event with no interval at all — retraining on a
changed safety data sheet, a fit test after a change to a worker's face, make
and model familiarisation on a machine nobody has operated before. A date-driven
engine reports those compliant forever. Where one exists it is named in the
artifact that owns it, so a reader is not left to infer it from a clean screen.

And a fourth distinction that matters even where the clock IS the law's: whether
being late invalidates something. A lapsed Working at Heights certificate makes
the work unlawful. An overdue committee meeting is a contravention and nothing
becomes invalid. The platform records the interval and its authority; the
consequence belongs in the artifact's text, and each one states it.

## Incidents are counted per job site, not per company

`cohs.incidents` carries a **relation** onto the project register rather than a
typed-in location, and that single column is why it exists separately from the
generic occupational health and safety programme's incident register. Every
question a constructor is actually asked is per job site — how many near misses
on this job, how many first aids this month, which of the eleven live sites is
carrying the exposure — and a free-text location cannot answer any of them,
because "Bay St", "Bay Street" and "bay st." are three sites to a machine.

It is also what makes `cohs.safety-statistics` honest. That register holds a
near-miss count and a first-aid count per month per account, and until now there
was nothing in the programme to count them FROM: they were integers somebody
typed in. They are now derivable from rows, and the statistics artifact requires
the incident register so the dependency is stated rather than assumed.

Near misses and first aid are both incidents here, and that is deliberate: a
register holding only lost time records the injuries that were not prevented,
which is the smallest and latest slice of what the organisation could have known.

## The crew problem, solved in the data

A pre-task hazard assessment happens once per crew per shift, and `applies_to`
has no vocabulary for a crew — deliberately, because a crew is not a scope this
platform has, and accepting the word would quietly map somebody's concept onto
ours. Writing `each project` instead is worse than useless: two crews on one
site become one expected record a day, one of them discharges it, and the
programme reports a hundred per cent while half the work is invisible.

So the expansion happens in the data. `cohs.daily-crew-assignments` holds one
row per crew per working day, and `cohs.pre-task-hazard-assessment` triggers off
it — one occurrence per row, due against that row's own date. Twenty crews
produce twenty expected assessments, and nineteen missing ones are nineteen
findings.

## The record-origin chains

Six chains are triggered by rows rather than by a calendar, because the work
has no period: a project has a start date, a credential has an expiry date, an
injury happens at a time.

    projects            → start-up duties · notice of project · designated substance list
    statutory credentials → renewal, 90 days before the card's own expiry
    WSIB clearances     → renewal, 14 days before the certificate's own expiry
    notifiable events   → the statutory notice, due 48 hours after the event
    project incidents   → investigation 3 days after it was reported
                          → corrective action 14 days after the investigation
                          → a monthly sweep of what is open and late
    work refusals       → the investigation, in the worker's presence

The incident chain is three links long and it terminates in a cadence, for the
reason the schema gives: the last link's verification would otherwise be
recorded in the register that triggered it, and every occurrence would discharge
itself at the moment it was created.

Each writes into a register other than the one that triggered it. A trigger
whose recording register is its own trigger register discharges every occurrence
at the moment it creates it, reporting completeness having checked nothing.

## What is deliberately not here

**Documented information.** `iso_45001:7.5` is answered by the document control
programme. Citing it here as well would double-count a gap one document closes.

**Code compliance.** The Ontario Electrical Safety Code, TSSA fuels, CWB
welding certification and the Ontario Building Code are standards this corpus
carries, and none of them is cited by an artifact here. They govern whether the
finished work is lawful; this programme governs whether the people building it
are safe. The two overlap in an organisation and not in a document, and an OHS
artifact claiming a building code control would be a compliance claim nobody
could defend at either end.

**Trade certification is the exception, and it is here.** Who may lawfully do
the work of a compulsory trade is a licensing question under the *Building
Opportunities in the Skilled Trades Act, 2021* rather than a safety one, and by
the paragraph above it would sit outside this programme. It is in it anyway, for
two reasons that are about the organisation rather than about the taxonomy: the
prohibition runs against **the employer** as well as the worker and reaches
anyone it "otherwise engages", so it is a duty discharged on site by the same
person doing the same walk; and the credential it turns on is already on this
programme's statutory credentials register, with the shortest expiry clock on
it. Splitting it into a programme of its own would have produced one artifact
that could not be checked without this one's data.

**Environmental protection, and the fleet.** Excess soil under O. Reg. 406/19,
spill reporting under the *Environmental Protection Act*, approvals from the
Ministry of the Environment, Conservation and Parks, and the *Highway Traffic
Act* regime that governs an operator's CVOR record, hours of service and load
securement all bind an Ontario construction company, and none of them is here.
They are genuinely absent rather than out of scope, and they are absent because
each is a programme rather than an artifact: a different regulator, a different
duty-holder inside the company, and a standard this corpus does not yet carry.
A constructor reading a clean screen here should not conclude that they have
been answered.

**Drug and alcohol testing, and short service employee programmes.** Both are
ISNetworld prequalification expectations with a distinctly American shape.
Ontario has no statutory testing regime, and a programme that shipped one as an
industry default would be asserting a legal basis that does not exist. An
organisation whose clients demand them adds them; the corpus does not assume
them.

**Anything the research could not verify.** No certificate interval, clause
number or standard edition appears here that could not be read from the
instrument itself. Where an interval is conventional, it is marked `chosen`.
Where the law is silent, the artifact says the law is silent — a confident zero
is worse than an honest gap, and in this domain a confident number is worse than
both.
