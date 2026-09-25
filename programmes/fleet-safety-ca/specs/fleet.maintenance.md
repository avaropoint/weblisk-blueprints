---
id: fleet.maintenance
kind: procedure
title: Preventive Maintenance Programme
structure: procedure
path: procedures/vehicle-maintenance-programme.md

satisfies:
  - hta_ontario:HTA-PMVI-03
  - hta_ontario:HTA-PMVI-04
  - hta_ontario:HTA-CVOR-03
  - nsc_ca:NSC-11
  - nsc_ca:NSC-15
  - cor_2020:COR-12
  - iso_45001:8.1.2

requires: [fleet.policy, fleet.vehicles, fleet.periodic-inspection]

declares:
  obligation:
    id: fleet.maintenance-service
    activity: Preventive maintenance service of the vehicle under the written maintenance programme
    cadence: each quarter
    authority: >
      No Ontario regulation prescribes a servicing interval for a commercial
      motor vehicle between periodic inspections. What binds is the operator's
      responsibility for the mechanical condition of its vehicles, and what
      tests it is the facility audit under National Safety Code Standard 15,
      which asks to see a planned maintenance programme and a record per vehicle
      of the work performed under it. The quarter is this organisation's default
      and is expected to be OVERRIDDEN per vehicle from the manufacturer's
      schedule, the duty cycle and the distance travelled — the vehicle
      register's `maintenance_interval` column is where that is recorded.
    interval_basis: chosen
    responsible: maintenance-lead
    applies_to: the organisation
    per:
      listed_in: registers/vehicles.md
      key: unit_number
      label: description
      from: in_service_on
      until: out_of_service_on
    records: registers/vehicle-maintenance-services.md
    escalate: {after: 4w, to: fleet-manager}
    satisfies:
      - hta_ontario:HTA-PMVI-03
      - nsc_ca:NSC-11
      - cor_2020:COR-12
  register:
    title: Vehicle Maintenance Service Record
    note: >
      One row per service, per vehicle. `interval_source` records where this
      vehicle's interval came from, because an interval nobody can attribute is
      one nobody will defend at an audit. `defects_raised` links the service back
      into the defect register rather than absorbing findings into a free-text
      note where the repair obligation never sees them.
    layout: form
    review: required
    approvers: [maintenance-lead]
    columns:
      - {key: vehicle, label: Vehicle, type: relation, required: true,
         target: /registers/vehicles.md#records, display: unit_number}
      - {key: serviced_on, label: Serviced on, type: date, required: true}
      - {key: odometer, label: Odometer reading, type: int, required: true}
      - {key: engine_hours, label: Engine hours, type: int}
      - {key: service_type, label: Service, type: select, required: true,
         options: ["Scheduled preventive service", "Safety-critical component check",
                   "Seasonal service", "Unscheduled — arising from a defect",
                   "Pre-periodic-inspection service", Other]}
      - {key: interval_source, label: Where this vehicle's interval comes from, type: select, required: true,
         options: ["Manufacturer's schedule", "Distance travelled",
                   "Engine hours", "Duty cycle judgement recorded in the procedure",
                   "Programme default", Not yet determined]}
      - {key: performed_by, label: Performed by, type: text, required: true}
      - {key: work_done, label: Work carried out, type: longtext, required: true}
      - {key: brakes_checked, label: Brake system checked and adjusted, type: bool, required: true}
      - {key: tyres_checked, label: Tyres and wheel fasteners checked, type: bool, required: true}
      - {key: defects_found, label: Defects found, type: longtext}
      - {key: defects_raised, label: Defect numbers raised in the defect register, type: text}
      - {key: parts, label: Parts fitted, type: longtext}
      - {key: cost, label: Cost, type: currency}
      - {key: invoice_reference, label: Invoice or work order number, type: text}
      - {key: next_service_due, label: Next service due, type: date}
      - {key: attachment, label: Work order or invoice, type: attachment}
    retention:
      keep: 2y
      authority: >
        No retention period is prescribed. Two years is this organisation's,
        chosen to cover the review period a facility audit works over, and the
        maintenance record per vehicle is the first thing that audit asks for.
      reason: A maintenance history the operator cannot produce is, at an audit, the same as no maintenance programme.
---

What this document must establish for THIS organisation: the written
maintenance programme itself — what is serviced, how often, on what basis, and
where the record for each vehicle lives.

**The distinction this artifact exists to protect is between a maintenance
history and a maintenance programme.** An operator that services by symptom has
a pile of invoices; an operator with a programme has an interval it can
attribute, a record per vehicle, and a way of showing that the interval was
kept. A facility audit asks for the second and is unmoved by the first, and the
difference is invisible from inside the organisation until somebody asks.

**No Ontario regulation sets a servicing interval, and the document must say
so.** What binds is the operator's responsibility for the mechanical condition
of its vehicles. Everything else — three months, five thousand kilometres, two
hundred and fifty engine hours — is the organisation's own number, and the
governance requirement is that it is written down, followed, and recorded. A
document that presents a quarterly service as a legal requirement has invented
an authority, and the first person to check will discount everything else in it.

**The quarterly default here is a starting point and is meant to be
overridden.** A float that does four thousand kilometres a year and a tandem
dump on a haul contract do not want the same interval, and the vehicle
register's `maintenance_interval` column exists so the real one is recorded per
vehicle rather than argued about. The procedure must say who sets it and on
what evidence — the manufacturer's schedule is the defensible answer and is
usually available.

**It must say what a service covers**, at least for the components the
regulation and the roadside care about: brakes and their adjustment, tyres and
wheel fasteners, steering and suspension, lights, and coupling devices. A
service sheet that is a tick beside "PM service" is a record of an appointment.

**A service that finds a defect must raise a defect**, in the defect register,
with a number — not a note in the work-order description. The repair obligation,
the out-of-service watch and the monthly review all read the defect register,
and a finding that never reached it is one nobody is tracking and nobody can
count.

**It must reach the vehicles the organisation does not own.** A leased unit, an
owner-operator's truck and a short-term rental are still the operator's
responsibility for mechanical condition if the operator is the operator of
record. The procedure must say what maintenance evidence is required from an
owner-operator and what happens when it does not arrive, because the answer
"they look after their own truck" is the organisation's answer at an audit
whether it meant it to be or not.
