---
id: cenv.dewatering-operations
kind: register
title: Register of Dewatering Operations
structure: standard
path: registers/dewatering-operations.md

# A register carries no `satisfies:`. The duty to authorise the taking and to
# keep the discharge lawful belongs to cenv.approvals-determination and
# cenv.dewatering, which declare the obligations over these rows.

requires: [cenv.environmental-approvals, cenv.excavation-projects]

register:
  title: Register of Dewatering Operations
  note: >
    One row per dewatering setup — a sump and pump, a wellpoint array, a
    deep-well system — not one per project. A single excavation frequently runs
    two: a sump discharging to a settling tank through the winter, and a
    wellpoint array for the deep section in June, with different rates, different
    discharge points and sometimes different instruments. They are the subjects
    the weekly discharge check multiplies over, so merging them into one row per
    site would produce one check a week covering two discharges and would credit
    the one nobody looked at.
    `started_on` and `ended_on` are the operation's life: a setup demobilised in
    August stops being expected in September, and a row left open is a discharge
    the programme still believes is running.
  columns:
    - {key: operation_id, label: Dewatering operation reference, type: text, required: true}
    - {key: area, label: Project area, type: relation, required: true,
       target: /registers/excavation-projects.md#records, display: area_id}
    - {key: description, label: What is being dewatered, type: text, required: true}
    - {key: method, label: Method, type: select, required: true,
       options: ["Sump and pump", "Wellpoint array", "Deep well", "Cut-off with pumped sump",
                 "Surface water diversion only", Other]}
    - {key: source, label: Water taken, type: select, required: true,
       options: ["Ground water", "Storm water", "Both", "Not yet determined"]}
    - {key: started_on, label: Dewatering started on, type: date, required: true}
    - {key: ended_on, label: Dewatering ended on, type: date}
    - {key: expected_duration_days, label: Expected duration, in days, type: int}
    - {key: beyond_365_days, label: Expected to run beyond 365 days, type: bool, required: true}
    - {key: peak_rate_litres_per_day, label: Highest expected taking, in litres a day, type: number, required: true}
    - {key: approval, label: Instrument authorising it, type: relation,
       target: /registers/environmental-approvals.md#records, display: approval_id}
    - {key: authorisation_route, label: How the taking is authorised, type: select, required: true,
       options: ["No instrument — 50,000 litres or less on every day",
                 "Registration in the Environmental Activity and Sector Registry",
                 "Permit to take water",
                 "Covered by an instrument held by the owner",
                 "Not yet determined"]}
    - {key: treatment, label: How the water is treated before discharge, type: longtext, required: true}
    - {key: discharge_point, label: Discharge point, type: text, required: true}
    - {key: receiving_body, label: What receives it, type: select, required: true,
       options: ["Ground on site — infiltration",
                 "Watercourse",
                 "Roadside ditch",
                 "Municipal storm sewer",
                 "Municipal sanitary sewer",
                 "Tankered off site",
                 "Not yet determined"]}
    - {key: municipal_consent, label: Municipal consent held where it discharges to a sewer, type: select, required: true,
       options: [Held, "Applied for", "Not required — no discharge to a sewer", Outstanding]}
    - {key: monitoring_required, label: Monitoring the instrument or the municipality requires, type: longtext}
    - {key: qualified_professional, label: Qualified professional who prepared the reports, type: text}
    - {key: status, label: Status, type: select, required: true,
       options: [Planned, Operating, Suspended, Complete]}
    - {key: note, label: Note, type: longtext}
---

What this artifact must establish for THIS organisation: every place it is taking
water out of the ground, how much, where it is going, and under what
authorisation.

It exists because **dewatering is the environmental activity a construction
company does most often and records least.** It starts because an excavation
filled up overnight, it is set up by whoever is on site, and it is the only thing
in this programme that can put this organisation in breach of two statutes within
an hour of somebody making a practical decision: taking more than 50,000 litres
on a day without an instrument, and discharging material that may impair the
quality of any waters.

**The register is per operation and not per project, and that is the load-bearing
decision.** One excavation running a winter sump and a summer wellpoint array is
two discharges with two rates, two treatment trains and sometimes two different
receiving bodies. The weekly discharge check multiplies over these rows, so a
register that held one row per site would expect one check a week between them,
and the first one filed would discharge the obligation for both.

**`peak_rate_litres_per_day` is required and it is a real number.** The 50,000
litre threshold in OWRA s. 34 is a daily ceiling, not an average, and it is
crossed by the pump running through a wet weekend rather than by anybody
deciding to cross it. A row with a blank rate cannot tell anybody whether an
instrument is owed, and "we are under the limit" without a figure is an opinion.

**`beyond_365_days` exists because it turns on a duty nobody expects.** Where a
taking registered in the Environmental Activity and Sector Registry will run
beyond 365 days, O. Reg. 63/16 requires notice to the municipalities and to any
conservation authority. That duty is invisible on day one and obvious on day
three hundred, by which time nobody is looking at the registration.

**`receiving_body` decides which other permissions are in play**, and it is the
field most likely to change without anybody recording it. A discharge moved from
infiltration on site to the roadside ditch because the ground stopped taking it
has changed statute — and a discharge to a municipal sewer needs the
municipality's consent under its sewer-use by-law, which no provincial approval
supplies. `municipal_consent` is asked of every row so that the answer "not
required" is a determination rather than a silence.
