---
id: cenv.spill-reporting
kind: procedure
title: Spill and Discharge Reporting
structure: procedure
path: procedures/spill-and-discharge-reporting.md

satisfies:
  - epa_ontario:91
  - epa_ontario:92
  - epa_ontario:93
  - epa_ontario:15
  - owra_ontario:30

requires: [cenv.environmental-incidents, cenv.policy]

declares:
  obligation:
    id: cenv.spill-reporting
    activity: Reportability decided, the Spills Action Centre and the municipality notified, and the notification recorded
    for:
      records: registers/environmental-incidents.md
      due: 24h after discovered_on
      key: incident_id
    authority: >
      Environmental Protection Act s. 92 and Ontario Water Resources Act s. 30
      require notification FORTHWITH, the duty taking effect the moment the
      person knows or ought to know. EPA s. 15 imposes the same word on a
      discharge out of the normal course of events not already caught by s. 92.
      There is no statutory period, because there is none to set. The
      twenty-four hours below is the deadline for the RECORD of the
      notification, never for the notification — a call made twenty-three hours
      after discovery is a contravention that this obligation would show as
      on time, which is why the register asks separately whether it was
      forthwith
    interval_basis: chosen
    responsible: environmental-lead
    applies_to: the organisation
    records: registers/spill-reports.md
    escalate: {after: 4h, to: senior-management}
  register:
    title: Spill and Discharge Report Record
    note: >
      One row per incident, including the incidents that were not reportable.
      `reportable` is a select over the actual statutory routes rather than a
      yes-or-no, because the three of them have different triggers and an
      organisation that records only "reported" cannot show which duty it
      thought it was discharging. "Not reportable" is an outcome and must be
      recordable as one with the ground beside it: O. Reg. 675/98's exemption
      for not more than 100 litres of fluid from a motor vehicle's fuel or
      operating system has three cumulative conditions, and a row asserting the
      exemption without them is a decision nobody can defend two years later.
    layout: form
    review: required
    approvers: [environmental-lead, senior-management]
    approval_order: sequential
    retention:
      keep: 7y
      authority: O. Reg. 675/98 requires a record of an unreported spill relied on as exempt to be kept for two years. Neither the Environmental Protection Act nor the Ontario Water Resources Act prescribes a period for the record of a reported spill
      reason: >
        Two years is the only prescribed figure and it applies to the weakest
        record in the set. Seven years is this organisation's, chosen to match
        the excess soil regulation's period so that one retention rule covers
        every environmental record rather than two that somebody has to keep
        apart — and because the limitation period for an offence and the memory
        of a neighbouring landowner both outlast two years comfortably.
    columns:
      - {key: incident, label: Incident, type: relation, required: true,
         target: /registers/environmental-incidents.md#records, display: incident_id}
      - {key: assessed_on, label: Reportability decided on, type: date, required: true}
      - {key: assessed_by, label: Decided by, type: user}
      - {key: reportable, label: Which duty applies, type: select, required: true,
         options: ["Reportable — a spill of a pollutant (EPA s. 92)",
                   "Reportable — a discharge out of the normal course of events (EPA s. 15)",
                   "Reportable — a discharge or escape affecting waters (OWRA s. 30)",
                   "Reportable under more than one of the above",
                   "Not reportable — O. Reg. 675/98 exemption, all three conditions held",
                   "Not reportable — no discharge into the natural environment",
                   "Not reportable — an instrument already requires it to be reported",
                   "Not yet determined"]}
      - {key: exemption_conditions, label: Which conditions of the exemption were checked, and how, type: longtext}
      - {key: sac_notified_on, label: Spills Action Centre notified on, type: date}
      - {key: sac_notified_time, label: Time the Spills Action Centre was notified, type: text}
      - {key: sac_reference, label: Spills Action Centre incident number, type: text}
      - {key: municipality_notified_on, label: Municipality notified on, type: date}
      - {key: municipality_notified_who, label: Who at the municipality was notified, type: text}
      - {key: owner_notified, label: Owner of the pollutant notified, type: select, required: true,
         options: ["Notified", "We are the owner", "Owner could not readily be ascertained", "Not applicable", Outstanding]}
      - {key: controller_notified, label: Person having control of the pollutant notified, type: select, required: true,
         options: ["Notified", "We had control", "Not applicable", Outstanding]}
      - {key: notified_by, label: Notification made by, type: user}
      - {key: information_given, label: What was said, against the O. Reg. 675/98 items, type: longtext}
      - {key: later_information, label: Information ascertained and given afterwards, type: longtext}
      - {key: corrections, label: Inaccuracies discovered later and corrected forthwith, type: longtext}
      - {key: reported_forthwith, label: Notification was made forthwith on the facts recorded, type: bool, required: true}
      - {key: delay_reason, label: If not forthwith, why, type: longtext}
      - {key: mitigation, label: What was done to prevent, eliminate and ameliorate the adverse effect, type: longtext, required: true}
      - {key: restoration, label: What was done to restore the natural environment, type: longtext, required: true}
      - {key: restoration_complete_on, label: Restoration complete on, type: date}
      - {key: regulator_attended, label: A provincial officer attended or an order was made, type: bool, required: true}
      - {key: order_reference, label: Order or direction reference, type: text}
      - {key: evidence, label: Call log, correspondence and any order, type: attachment}
      - {key: note, label: Note, type: longtext}
---

What this document must establish for THIS organisation: who telephones the
Spills Action Centre, who telephones the municipality, what they say, and — the
part that is actually hard — how somebody standing in a trench at six in the
morning decides which of those calls is owed.

It must state the duty in the words the Act uses. Every person having control of
a pollutant that is spilled, and every person who spills or causes or permits a
spill, shall **forthwith** notify the Ministry, the municipality within whose
boundaries the spill occurred, the owner of the pollutant where they are not the
owner and can readily ascertain who is, and the person having control of it. The
duty takes effect **the moment the person knows or ought to know** the pollutant
is spilled. It is discharged by telephoning the Spills Action Centre, and
O. Reg. 675/98 prescribes what must be said: the location, the time the discharge
was discovered and the time it occurred, the pollutant and the quantity, the
cause or the best assessment of it, the adverse effects that occurred or may
occur, and who is responsible for each action being taken. **Information not
available at the time must be ascertained and provided forthwith, and an
inaccuracy discovered later must be corrected forthwith** — two duties that are
almost universally missed, because the first call feels like the end of the
obligation and it is the beginning of it.

**Four notifications, not one.** The municipality is a separate call and it is
the one that gets skipped, because nobody in a construction organisation has a
number for it and the Spills Action Centre does not pass it on. The procedure
must name, for each municipality this organisation habitually works in, who is
telephoned out of hours — and must say that where it does not know, the call goes
to the municipality's own emergency line rather than not being made.

**Section 93 is a duty in its own right and it does not wait for the call.** The
owner of the pollutant and the person having control of it shall forthwith do
everything practicable to prevent, eliminate and ameliorate the adverse effect
and to restore the natural environment, judged against the technical, physical
and financial resources that are or can reasonably be made available. It is owed
independently of whether anybody has been notified, and a procedure that sequences
containment after the telephone call has the order wrong. What the platform can
show is that both happened and when.

**The exemption must be stated with all three of its conditions or not at all.**
O. Reg. 675/98 relieves the duty to notify for not more than 100 litres of fluid
from the fuel or operating system of a motor vehicle **where** it does not and is
not likely to enter waters directly or through a drainage structure, **and** it
causes no adverse effect other than one readily remediated from a prepared
surface, **and** remediation is arranged and carried out immediately. The
conditions are cumulative. A hundred litres of diesel on gravel beside a catch
basin meets the first and fails the second and third, and a record of an
unreported exempt spill must be kept for two years — which is to say the
exemption is proved by writing it down, not by staying quiet.

**Twenty-four hours is this organisation's and the statute's period is none.**
The programme cannot express "forthwith", and a deadline that pretended to would
be a worse lie than an honest one. The twenty-four hours is the point at which a
record of the call is expected to exist; `reported_forthwith` is where the
programme records whether the call itself was timely, and it is asked as a
separate question precisely so that a late call cannot hide behind a punctual
form. The escalation after four hours to senior management exists for the same
reason: an incident on which nobody has recorded a decision by lunchtime is one
where the decision is being avoided rather than made.

It must say what happens when **a sub-trade or a hauler spilled it**. The duty
falls on the person having control of the pollutant, which includes their
employee or agent, and on the person who causes or permits the spill. Where this
organisation is the constructor and the incident is on its site, the safe and
usually correct assumption is that the duty is ours as well as theirs, and the
call is made rather than negotiated.
