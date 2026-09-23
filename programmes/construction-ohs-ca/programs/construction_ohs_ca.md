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
  - { id: cohs.return-to-work, tier: conformant }
  - { id: cohs.management-review, tier: conformant }
  # ── certifiable: it audits itself and produces what is asked for ───────────
  - { id: cohs.ohsms-audit, tier: certifiable }
  - { id: cohs.safety-statistics, tier: certifiable }
---

Forty-three artifacts for a constructor or employer working on construction
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

Thirty-six of the forty-three artifacts sit at `essential`, and that is the
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

Four chains are triggered by rows rather than by a calendar, because the work
has no period: a project has a start date, a credential has an expiry date, an
injury happens at a time.

    projects            → start-up duties · notice of project · designated substance list
    statutory credentials → renewal, 90 days before the card's own expiry
    WSIB clearances     → renewal, 14 days before the certificate's own expiry
    notifiable events   → the statutory notice, due 48 hours after the event

Each writes into a register other than the one that triggered it. A trigger
whose recording register is its own trigger register discharges every occurrence
at the moment it creates it, reporting completeness having checked nothing.

## What is deliberately not here

**Documented information.** `iso_45001:7.5` is answered by the document control
programme. Citing it here as well would double-count a gap one document closes.

**Trade licensing and code compliance.** The Ontario Electrical Safety Code,
TSSA fuels, CWB welding certification and the Ontario Building Code are
standards this corpus carries, and none of them is cited by an artifact here.
They govern whether the finished work is lawful; this programme governs whether
the people building it are safe. The two overlap in an organisation and not in a
document, and an OHS artifact claiming a building code control would be a
compliance claim nobody could defend at either end.

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
