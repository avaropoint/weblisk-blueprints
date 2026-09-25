---
id: fleet_safety_ca
title: Commercial Fleet Safety Programme (Canada — Ontario)
order: 22
domains:
  - health_safety
  - equipment_integrity
  - trade_regulatory
  - training_competency
  - records_management
  - compliance_audit
conforms_to:
  - hta_ontario
  - nsc_ca
  - mvta_canada
  - cor_2020
  - iso_45001

tiers:
  - id: statutory
    title: Lawful to put a vehicle on the road
    rationale: >
      What an Ontario company operating commercial motor vehicles must have in
      place before a vehicle is driven. Every artifact at this line answers a
      duty that exists on the day the truck leaves the yard — the certificate the
      operator holds, the inspection the driver owes before moving, the hours the
      driver may work, the securement of what is on the deck, the class of
      licence held, and the sticker on the windscreen. Below this line the
      organisation is not unaccredited, it is operating unlawfully, and the
      consequence is not a finding at an audit: it is an out-of-service order at
      the roadside and an entry on a record that decides whether the company may
      go on operating at all.
  - id: auditable
    title: It survives a facility audit
    requires: statutory
    rationale: >
      A facility audit under National Safety Code Standard 15 examines the
      operator's own records rather than its vehicles, and the finding that
      decides its outcome is usually an absence rather than a defect. This tier
      is what turns a compliant week into a defensible year: a written
      maintenance programme with a record per vehicle, a collision looked at
      rather than merely reported, and somebody reading the whole of it on a
      cycle instead of at the point the Ministry writes a letter. Nothing here
      is required by the Highway Traffic Act. All of it is asked for by an
      auditor, by an insurer, and by the first serious claim.

# ── the standing work adopting this programme takes on ──────────────────────
#
# A fleet programme that is not running is a binder of forms on a shelf and a
# CVOR record accumulating in the dark. These four are the things that must
# actually happen: somebody is told what is due before the trucks roll, the
# instruments that let a driver and a vehicle be on the road are looked at
# before they lapse, an open major defect is not allowed to age quietly, and
# the exposure the record is building is read on a cycle.
#
# Every one is created PAUSED. Turning them on is one switch each, and the
# switch is the organisation's.
operations:
  - id: due-sweep
    title: What is due
    does: due-sweep
    schedule: {cadence: daily, at: "05:30"}
    why: >
      A trip inspection is owed before the vehicle is driven, and vehicles are
      driven early. A list of what is due today is of use only to somebody who
      can still act on it, so this runs before the yard opens rather than at the
      start of an office day. It reports and never remediates.

  - id: currency-watch
    title: Licences, medicals and inspection stickers
    agent: >
      Report on the instruments that decide whether a driver may drive and a
      vehicle may be on the road.

      Read registers/drivers.md, registers/vehicles.md,
      registers/licence-renewals.md and registers/periodic-inspections.md. For
      every active driver report the licence class and endorsements held, the
      licence expiry, and the date the licence was last verified against the
      Ministry's record rather than against a photocopy. For every vehicle in
      service report the date the periodic inspection sticker expires and
      whether a booking exists.

      Separate three states and never merge them. LAPSED — the licence or the
      sticker has expired and the driving or the vehicle should have stopped.
      EXPIRING — it falls due inside sixty days and somebody has to act now.
      UNKNOWN — the register has no row, or the row has no date, which is not
      the same as current and must never be reported as such.

      Say plainly where a register could not be read. A check that could not
      parse its source has refuted nothing, and an empty result reported as a
      clean one is worse than no report.

      Do not write any file, do not create any document request, and do not
      contact any driver: this is a report to the people who can.
    needs: [read]
    schedule: {cadence: weekly, at: "06:30", weekday: monday}
    why: >
      A licence and a sticker both expire on a date somebody else set, so
      neither can be derived from a cadence and both have to be looked at. On a
      Monday, because the question is which of our vehicles and drivers may
      lawfully work this week.

  - id: out-of-service-watch
    title: Open major defects, and vehicles that should not be moving
    agent: >
      Report on every vehicle defect that is open.

      Read registers/vehicle-defects.md, registers/defect-repairs.md and
      registers/trip-inspections.md. List every defect whose status is not
      closed, and for each give the vehicle, when it was reported, how it was
      reported, and whether it was classified as major or minor.

      Then answer the question that matters: is any vehicle with an OPEN MAJOR
      defect recorded as still in service, or appearing on a trip inspection
      after the date the defect was reported? A major defect means the vehicle
      must not be driven, and a vehicle that kept moving is not a paperwork
      finding — name it first and name it plainly.

      Report separately any defect whose classification is missing. A defect
      with no classification has not been decided about, and it is not a minor
      one by default.

      Do not write any file and do not contact anybody. State what could not be
      read rather than passing over it.
    needs: [read]
    on: [obligation.overdue]
    schedule: {cadence: daily, at: "16:00"}
    why: >
      Two clocks on purpose. The event catches a repair going past its deadline
      on the day it happens; the afternoon sweep catches the day on which
      nothing fired because the server was down, and runs late enough to see
      what the day's trip inspections found. This is the one report in the
      programme where the answer can be that a vehicle is on the road and
      should not be.

  - id: programme-readiness
    title: Programme readiness
    does: programme-readiness
    schedule: {cadence: monthly, at: "07:00", day: 1}
    why: >
      Both numbers on a cycle: how much of the programme exists as current,
      cited documents, and how much of it is producing attested records. Monthly
      rather than weekly because a programme does not move week to week. It
      reports; it never drafts what it finds missing.

artifacts:
  # ── statutory: lawful to put a vehicle on the road ─────────────────────────
  - { id: fleet.policy, tier: statutory }
  - { id: fleet.vehicles, tier: statutory }
  - { id: fleet.drivers, tier: statutory }
  - { id: fleet.cvor, tier: statutory }
  - { id: fleet.driver-qualification, tier: statutory }
  - { id: fleet.licence-renewal, tier: statutory }
  - { id: fleet.hours-of-service, tier: statutory }
  - { id: fleet.trip-inspection, tier: statutory }
  - { id: fleet.vehicle-defects, tier: statutory }
  - { id: fleet.defect-repair, tier: statutory }
  - { id: fleet.load-securement, tier: statutory }
  - { id: fleet.periodic-inspection, tier: statutory }
  - { id: fleet.collisions, tier: statutory }
  # ── auditable: it survives a facility audit ────────────────────────────────
  - { id: fleet.collision-review, tier: auditable }
  - { id: fleet.maintenance, tier: auditable }
  - { id: fleet.compliance-review, tier: auditable }
---

Sixteen artifacts for an Ontario company that operates commercial motor
vehicles — which, for a general contractor, means almost any company with a
tandem dump, a float, a boom truck or a tow truck in the yard.

## Who this programme is for, and who must not adopt it

**The line is 4,500 kg.** A truck, or a truck and trailer combination, with a
registered gross weight or an actual weight of more than 4,500 kg puts the
company into the Commercial Vehicle Operator's Registration regime. Buses are
caught by seating capacity instead, and tow trucks are caught regardless of
either. A company whose vehicles are all pickups, vans and cars below that
weight is **outside every duty in this programme** and should not adopt it.

That is not a caveat, it is the most consequential sentence here. Adopting a
programme that does not apply does not produce a cautious organisation; it
produces a plan full of obligations that will never be discharged, because there
is no vehicle to inspect, no driver's hours to audit and no abstract to read.
Those gaps can never be closed, they depress every readiness number the platform
reports, and after a few months of that nobody believes any of the numbers. A
company with no vehicle over 4,500 kg should decline this programme and, if it
wants its light vehicles governed, write a short driving-at-work policy against
its occupational health and safety programme instead. **A company that is
uncertain reads the exception list in the Act rather than guessing**, because it
is the list and not the weight that decides the edge cases, and a company that
is partly in — one float among forty pickups — is fully in for that float.

## The federal and the provincial halves, which are not interchangeable

This is the distinction the programme is built around, and blurring it is how a
carrier ends up keeping the wrong records competently.

The **National Safety Code** ([`nsc_ca`](../../standards/README.md)) is a set of
model standards agreed by the federal, provincial and territorial governments
through CCMTA. **It is not law anywhere.** It binds only through the instruments
that adopt it.

**Ontario** adopts it for **intra-provincial** operation:
[`hta_ontario`](../../standards/README.md) carries the *Highway Traffic Act* and
O. Reg. 555/06 (hours of service), O. Reg. 199/07 (trip inspection),
O. Reg. 363/04 (security of loads) and R.R.O. 1990, Reg. 611 (periodic
inspection). A carrier whose vehicles stay inside Ontario is under these.

**Canada** adopts it for **extra-provincial** operation:
[`mvta_canada`](../../standards/README.md) carries the *Motor Vehicle Transport
Act* and the *Commercial Vehicle Drivers Hours of Service Regulations*. A
carrier whose vehicles cross a provincial, territorial or international boundary
is an extra-provincial undertaking for that work, and is under the federal
regulation for it.

Three consequences that a contractor running mostly local work gets wrong:

- **It turns on where the vehicle goes, not where the company is based.** An
  Ontario company that sends one float to Gatineau twice a year is
  extra-provincial for those trips and for the hours records behind them.
- **The numbers are the same and the instrument is not.** Thirteen hours
  driving, fourteen on duty, seventy in seven days — identical on both sides. So
  nothing goes visibly wrong until somebody asks which regulation the record was
  kept under, and by then the answer is fixed.
- **The CVOR certificate is the same piece of paper either way.** Ontario's CVOR
  serves as the safety fitness certificate for an Ontario-based extra-provincial
  carrier, so there is no moment at which the company is issued something new
  and notices. `registers/drivers.md` therefore carries an
  `operates_extra_provincially` column, because a fact nobody records is a fact
  nobody checks.

## The CVOR record is the asset this programme protects

Everything else here is a duty about a vehicle or a driver. The CVOR record is a
duty about the company, and it is the only one whose failure stops the whole
operation at once.

The Ministry keeps a record for every registered operator: reportable
collisions, convictions of the operator and of its drivers, the results of
roadside inspections and any out-of-service order. Each event is weighted and
each falls off after a fixed period, so the record is a rolling window. The
weighted total is measured against the operator's *exposure* — fleet size and
distance travelled — to produce a **violation rate expressed as a percentage of
a threshold**, and the Ministry escalates along a published ladder: a warning
letter, then an interview, then a facility audit, then sanction, suspension or
cancellation.

Two things follow, and `fleet.cvor` exists for both.

**Nothing tells the operator.** The record accumulates silently. The abstract is
the only view of it the operator gets, and obtaining one is the operator's own
act. An operator that has never ordered an abstract first hears about its record
in the letter, at which point the events being complained of are two years old
and unalterable. The quarterly abstract review is marked `interval_basis:
chosen` because no instrument requires it — and it is in the `statutory` tier
anyway, because it is the only obligation here that can see the others failing.

**Growth moves the rate without anything getting worse.** The denominator is
fleet size and kilometres declared to the Ministry. A company that has doubled
its fleet and not updated its registration is being measured against an exposure
it no longer has, in the wrong direction. That is why
`HTA-CVOR-07` is cited and why the abstract review records the declared figures
alongside the rate.

## The 160 km exemption, done properly

Most construction fleets in Ontario operate under the radius exemption, and it
is the provision they are most often told — wrongly — that they cannot use. A
driver need not fill out a daily log where three conditions all hold: the driver
operates within a radius of 160 km of the home terminal, returns to the home
terminal to begin at least eight consecutive hours off duty, and **the operator
keeps accurate and legible records showing the driver's on-duty times and the
hour at which each duty status began and ended.**

Get the three things right about it that decide whether an operator is actually
inside it:

1. **It exempts the log and nothing else.** Thirteen hours driving, fourteen on
   duty, ten off with eight consecutive, the cycle — all of them apply in full,
   and the operator must still be able to show they were met.
2. **It is conditional day by day, not a status a driver holds.** One trip
   beyond the radius, or one night not spent at the home terminal, means *that
   day* required a log. A driver marked "log exempt" in a spreadsheet is a
   driver nobody is checking.
3. **The time record is a condition of the exemption, not an alternative to
   record-keeping.** An operator keeping no time record has not used the
   exemption. It has no hours records at all.

So `fleet.hours-of-service` audits a driver on whichever basis actually applied,
and its register carries `exemption_conditions_held` and
`days_requiring_a_log_without_one` as separate columns from the limit breaches.
A programme that simply recorded "exempt" would report a clean month for a fleet
that had been outside the radius all of it.

## Three kinds of clock, and never blended

Ontario commercial vehicle regulation sets very few intervals. Most of what
circulates as a fleet compliance calendar is convention or an insurer's
preference, so every obligation here declares `interval_basis`:

- **`required`** — the interval is the instrument's. There is exactly **one** in
  this programme: the trip inspection, because O. Reg. 199/07 requires the
  inspection before the vehicle is driven on a day and makes the report valid
  for twenty-four hours.
- **`chosen`** — the authority requires the activity, or makes the operator
  answerable for the outcome, and sets no interval. The CVOR abstract review,
  the driver abstract, the hours audit, the securement check, the maintenance
  service, the monthly sweep: every one of those numbers is this organisation's,
  and each artifact says so in words.

There is a third case the schema cannot express and the prose therefore must:
the **periodic inspection**. Its twelve-month validity *is* the law's, but what
the programme can trigger on is the sticker's own expiry date, so the obligation
is record-origin and the thirty days of notice is ours. `interval_basis: chosen`
there means "the thirty days is chosen", never "the twelve months is optional",
and `fleet.periodic-inspection`'s brief says so.

And a distinction that matters even where the clock is the law's: **whether
being late invalidates something.** A driver whose licence has expired may not
drive — the work stops. A maintenance service a month late is a gap in a
programme and nothing becomes unlawful. The platform records the interval and
its authority; the consequence belongs in each artifact's text, and each one
states it.

## Per vehicle and per driver, in the data

Almost nothing in a fleet programme happens once for the company. A trip
inspection is one occurrence per vehicle per day; an hours audit is one per
driver per month. `applies_to` has no vocabulary for either, deliberately, and
writing `each project` would mean one trip inspection a day for a yard of
thirty vehicles — one truck discharging the obligation for all of them, and a
programme reporting a hundred per cent while twenty-nine vehicles went out
uninspected.

So the expansion happens in the data. `registers/vehicles.md` and
`registers/drivers.md` are standing registers whose rows are the subjects, each
with a `from` and an `until` column so a vehicle sold in March stops being
expected in April, and every recording register carries a relation column back
onto the subject.

Which makes the **vehicle register's boundary load-bearing**. It holds
commercial motor vehicles — the ones over 4,500 kg that sit on the CVOR fleet —
and a company that pads it with pickups has manufactured several hundred
obligations a year that no law asks for and that nobody will do. The register's
own brief says so, and `cvor_vehicle` is a required column rather than an
assumption.

## The record-origin chains

Four obligations are triggered by rows rather than by a calendar, because the
work has no period — a defect is found at a moment, a collision happens at a
time, a licence expires on a date:

    drivers            → licence renewal, 60 days before the licence expires
    vehicles           → periodic inspection, 30 days before the sticker expires
    vehicle defects    → the repair decision, 24 hours after it was reported
    collisions         → the collision review, 14 days after it occurred

Each writes into a register other than the one that triggered it, and both
chains that could continue — defects and collisions — terminate in
`fleet.compliance-review`'s monthly sweep. A trigger whose recording register is
its own trigger register discharges every occurrence at the moment it creates
one, reporting completeness having checked nothing.

## What is deliberately not here

**Dangerous goods.** The *Transportation of Dangerous Goods Act, 1992* and its
regulations, the training certificate and its thirty-six-month period, placarding
and shipping documents, and the emergency response assistance plan are a
programme of their own with a different regulator and a different duty-holder.
A contractor hauling fuel, propane cylinders or a waste stream is under them and
will find nothing here that answers them.

**Vehicle weights and dimensions, and permits.** Axle weights, overall
dimensions, the half-load season on designated roads, and the oversize or
overweight permit a float needs are Highway Traffic Act duties and are genuinely
absent. They are an economic and infrastructure regime rather than a safety one,
they are enforced by weight rather than by record, and a contractor moving
equipment needs them. They are absent, not answered.

**Driver training, drug and alcohol testing, and telematics.** Mandatory Entry
Level Training is a licensing condition administered between the driver and the
Ministry, not a duty on the carrier. Ontario has no statutory testing regime for
commercial drivers, and a programme that shipped one as an industry default
would assert a legal basis that does not exist — a carrier doing cross-border
work is a different matter and is under the United States regime for it.
Telematics and camera policy are governed by Ontario's electronic monitoring
duty, which is in the employment programme.

**Anything the research could not verify.** No interval, threshold or clause
appears here that could not be read from the instrument. The Ministry's CVOR
intervention percentages are administrative, published in its *Commercial
Vehicle Operator's Safety Manual*, and change without an amendment — so they are
described as a ladder and the figures are to be read from the Ministry rather
than from this corpus. Where the law is silent, the artifact says the law is
silent.
