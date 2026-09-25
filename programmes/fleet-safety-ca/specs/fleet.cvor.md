---
id: fleet.cvor
kind: procedure
title: CVOR Certificate and Safety Record Monitoring
structure: procedure
path: procedures/cvor-record-monitoring.md

satisfies:
  - hta_ontario:HTA-CVOR-01
  - hta_ontario:HTA-CVOR-02
  - hta_ontario:HTA-CVOR-03
  - hta_ontario:HTA-CVOR-04
  - hta_ontario:HTA-CVOR-05
  - hta_ontario:HTA-CVOR-06
  - hta_ontario:HTA-CVOR-07
  - nsc_ca:NSC-07
  - nsc_ca:NSC-14
  - mvta_canada:MVTA-01
  - mvta_canada:MVTA-02

requires: [fleet.policy, fleet.vehicles]

declares:
  obligation:
    id: fleet.cvor-abstract-review
    activity: Obtain and review the operator's CVOR abstract, and confirm the registered information is current
    cadence: each quarter
    authority: >
      Highway Traffic Act Part II — the Ministry maintains a safety record for
      every registered operator and issues an abstract of it on request, and the
      operator must keep its registered information current. Nothing in the Act
      requires the operator to read its own record and no interval is set
      anywhere. The quarter is this organisation's, chosen because events stay
      on the record for a rolling period of years and the Ministry's ladder is
      climbed in silence — an annual look finds an intervention that is already
      three quarters old and unanswerable.
    interval_basis: chosen
    responsible: fleet-manager
    applies_to: the organisation
    records: registers/cvor-abstract-reviews.md
    escalate: {after: 2w, to: senior-management}
    satisfies:
      - hta_ontario:HTA-CVOR-04
      - hta_ontario:HTA-CVOR-05
      - hta_ontario:HTA-CVOR-07
      - nsc_ca:NSC-14
  register:
    title: CVOR Abstract Review Record
    note: >
      One row per abstract obtained and read. `declared_fleet_size` and
      `declared_kilometres` are recorded beside the rate because they are its
      DENOMINATOR: a rate that moved without the events changing has usually
      moved because the exposure declared to the Ministry is out of date.
      `unexpected_events` is required because an entry the organisation did not
      know about is the most valuable line in this register — it is usually a
      collision or a conviction a driver did not report.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: obtained_on, label: Abstract obtained on, type: date, required: true}
      - {key: abstract_type, label: Kind of abstract, type: select, required: true,
         options: ["Operator's own record — the fuller abstract",
                   "Summary abstract available on the CVOR number",
                   Other]}
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: cvor_number, label: CVOR number, type: text, required: true}
      - {key: certificate_status, label: Certificate status, type: select, required: true,
         options: [Valid, "Valid — conditions imposed", Under conduct review,
                   Suspended, Cancelled, Not yet determined]}
      - {key: violation_rate, label: Violation rate on the abstract (% of threshold), type: percent}
      - {key: rate_read_from, label: Where the intervention thresholds were read from, type: text, required: true}
      - {key: declared_fleet_size, label: Fleet size declared to the Ministry, type: int, required: true}
      - {key: actual_fleet_size, label: Vehicles actually operated, type: int, required: true}
      - {key: declared_kilometres, label: Annual kilometres declared to the Ministry, type: int}
      - {key: registered_information_current, label: Name, address, officers, fleet and distance all current, type: bool, required: true}
      - {key: collisions_on_record, label: Collisions on the record, type: int, required: true}
      - {key: convictions_on_record, label: Convictions on the record, type: int, required: true}
      - {key: inspections_on_record, label: Roadside inspections on the record, type: int, required: true}
      - {key: out_of_service_orders, label: Out-of-service orders on the record, type: int, required: true}
      - {key: unexpected_events, label: Entries the organisation had not recorded itself, type: longtext, required: true}
      - {key: ministry_correspondence, label: Letters, interviews or audits notified since the last review, type: longtext}
      - {key: intervention_stage, label: Where the operator stands on the intervention ladder, type: select, required: true,
         options: ["No intervention", "Warning letter", "Interview",
                   "Facility audit", "Sanction, suspension or cancellation",
                   Not yet determined]}
      - {key: actions, label: Actions decided, with owners and dates, type: longtext, required: true}
      - {key: next_review, label: Next review due, type: date}
    retention:
      keep: 7y
      authority: >
        No retention period is prescribed for an abstract or for an operator's
        review of it. Seven years is this organisation's, chosen so that the
        record covers more than one full turn of the rolling window the Ministry
        measures over, and so a conduct review can be answered with the
        organisation's own contemporaneous reading of the same events.
      reason: A conduct review examines a period the organisation can no longer change; what it can produce is evidence that it was watching.
---

What this document must establish for THIS organisation: that somebody orders
the CVOR abstract, reads it, and does something about what is on it.

**This is the only duty in the programme that is about the company rather than
about a vehicle or a driver, and it is the only one whose failure stops
everything at once.** A suspended or cancelled certificate means the
organisation's commercial motor vehicles may not be driven, whatever condition
they are in and whoever is available to drive them.

**Nothing tells the operator.** The record accumulates silently: reportable
collisions, convictions of the operator and of its drivers, the results of
roadside inspections and any out-of-service order, each weighted by severity
and each falling off after a fixed period. The abstract is the only view of it
the operator gets and obtaining one is the operator's own act. The procedure
must name who orders it, how, and what they do with it — an organisation that
has never ordered one first learns its position from a letter about events two
years old.

**The thresholds are administrative and must be read from the Ministry, not
from this corpus.** The violation rate is expressed as a percentage of a
threshold and the Ministry escalates along a published ladder — warning letter,
interview, facility audit, then sanction, suspension or cancellation. The
percentages at which each step is taken are published in the Ministry's
*Commercial Vehicle Operator's Safety Manual* and change without an amendment
to the Act. The procedure must therefore tell the reader **where to look them
up**, and `rate_read_from` records that they did. A document that hard-codes
four numbers is a document that will be confidently wrong on a date nobody
noticed.

**The rate moves when the fleet grows, and nothing has got worse.** The
denominator is the operator's exposure — fleet size and distance travelled, as
declared to the Ministry. A company that has doubled its fleet without updating
its registration is measured against an exposure it no longer has, in the
direction that hurts. Keeping the registered information current is a statutory
duty in its own right, and it is done here rather than in a separate annual
task because the abstract is the moment somebody is already looking at the
figures.

**It must say what the organisation does when an entry appears that it did not
know about.** That is the finding this review exists to produce. A collision on
the record with no row in the collision register, or a conviction against a
driver the organisation was not told about, is a failure of internal reporting
and not of the Ministry's record-keeping — and the procedure must route it back
into the collision review and the driver's file rather than leaving it as a
discrepancy somebody noted.

**It must cover the certificate as a physical thing too.** The certificate, or
a copy of it, is carried in the vehicle and produced on demand, and a renewal
cycle the Ministry sets applies to it. That is a small duty beside the record,
and it is the one that produces a charge at the roadside.

**The quarterly interval is this organisation's.** The Act requires no review
at all. What the procedure should say is why a quarter and not a year: the
ladder is climbed by events the operator generated and could have seen coming,
and an intervention is answered before it is opened or not at all.
