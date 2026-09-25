---
id: cenv.approval-conditions
kind: procedure
title: Approval Condition Compliance
structure: procedure
path: procedures/approval-condition-compliance.md

satisfies:
  - epa_ontario:20.2
  - epa_ontario:20.21
  - owra_ontario:53

requires: [cenv.environmental-approvals]

declares:
  obligation:
    id: cenv.approval-conditions
    activity: Each instrument's conditions checked against what the site is actually doing, and the monitoring and reporting they require confirmed as done
    cadence: each quarter
    per:
      listed_in: registers/environmental-approvals.md
      key: approval_id
      label: number
      from: effective_from
      until: expires_on
    authority: >
      Environmental Protection Act ss. 9, 20.21 and 27 and Ontario Water
      Resources Act s. 53 prohibit the activity except "under and in accordance
      with" the instrument, and s. 20.2 makes the Director's terms and
      conditions the operative requirement. O. Reg. 63/16 sets dated duties of
      its own — an annual report of daily volumes on or before 31 March,
      immediate notification of any complaint relating to the natural
      environment. None of them requires the holder to audit itself, and none
      sets an interval for doing so. Each quarter is this organisation's,
      chosen so that an annual reporting condition is looked at three times
      before it falls due rather than once after
    interval_basis: chosen
    responsible: environmental-lead
    applies_to: the organisation
    records: registers/approval-condition-checks.md
    escalate: {after: 2w, to: project-manager}
  register:
    title: Approval Condition Check
    note: >
      One row per instrument per quarter while it is in force. The row is not a
      certificate that everything is fine; `conditions_met` has an option for a
      condition that was not met and was reported, because several instruments
      require the holder to tell the Director when they breach one, and a
      register with no way to say so turns a reporting duty into a concealment.
      `complaints_received` is an integer and not a boolean on purpose — under
      O. Reg. 63/16 a complaint relating to the natural environment must be
      notified immediately, so the number of them is a fact with a duty attached
      rather than a satisfaction metric.
    layout: form
    review: required
    approvers: [environmental-lead]
    retention:
      keep: 5y
      authority: O. Reg. 63/16 requires records relating to an activity registered in the Environmental Activity and Sector Registry to be retained for five years
      reason: >
        Five years is the prescribed period for the instrument with the most
        detailed record-keeping conditions in this register, and it is applied
        to every instrument's check rather than sorted per row. A retention rule
        that depends on which instrument a row happens to cite is one that will
        be applied wrongly the first time somebody disposes of a year's records.
    columns:
      - {key: approval, label: Approval, type: relation, required: true,
         target: /registers/environmental-approvals.md#records, display: approval_id}
      - {key: period, label: Quarter checked, type: text, required: true}
      - {key: checked_on, label: Checked on, type: date, required: true}
      - {key: checked_by, label: Checked by, type: user}
      - {key: activity_matches_instrument, label: What the site is doing is what the instrument authorises, type: bool, required: true}
      - {key: conditions_met, label: Conditions, type: select, required: true,
         options: ["All conditions met",
                   "Met, with the exceptions recorded below",
                   "A condition was not met — reported to the Director",
                   "A condition was not met — not yet reported",
                   "Not yet determined"]}
      - {key: monitoring_done, label: Monitoring and sampling the conditions require was done, type: select, required: true,
         options: ["Done as required", "Partly done", "Not done", "No monitoring conditions"]}
      - {key: monitoring_results, label: What the monitoring showed, type: longtext}
      - {key: exceedances, label: Results outside a limit the instrument sets, type: longtext}
      - {key: reporting_due, label: Reporting falling due before the next check, type: longtext}
      - {key: annual_report_filed_on, label: Annual report filed on, type: date}
      - {key: complaints_received, label: Complaints relating to the natural environment received, type: int, required: true}
      - {key: complaints_notified, label: Every complaint notified as the instrument requires, type: bool, required: true}
      - {key: records_kept, label: The records the instrument requires are being kept, type: bool, required: true}
      - {key: exceptions, label: What was not met, and what is being done, type: longtext}
      - {key: evidence, label: Monitoring records and correspondence, type: attachment}
      - {key: note, label: Note, type: longtext}
---

What this document must establish for THIS organisation: who reads the conditions
of an instrument it holds, how often, and what happens when the site has drifted
away from them.

It exists because **the offence is operating otherwise than in accordance with an
approval, not operating without one.** Nobody in this industry forgets to get an
approval — an approval is a gate and the job stops at it. What happens instead is
that the approval is obtained, the job changes, and eighteen months later the
site is doing something the instrument does not describe: a different discharge
point, a higher rate, a piece of plant that was not in the application. The
instrument is still on the wall and it authorises something else.

**`activity_matches_instrument` is the first question and it is not about
paperwork.** It asks whether what the site is physically doing is what the
Director approved. A discharge relocated fifty metres to a different ditch, a
crusher moved inside a setback, a taking that went from 40,000 to 70,000 litres
on the day the sump was deepened — each of those is a change to the authorised
activity and each of them happens on a Tuesday without a document.

**The EASR registration is the instrument this obligation earns its place for.**
Because registration is instantaneous and unassessed, the conditions in
O. Reg. 63/16 are the only thing standing between a registered activity and an
unlawful one, and they are substantial: records of daily volumes, an **annual
report to the Director on or before 31 March**, **immediate** notification of any
complaint relating to the natural environment, notice to the municipalities and
any conservation authority where the taking will run beyond 365 days, and
five-year retention. An organisation that registered a dewatering in April and
has not thought about it since is not compliant; it is unaudited.

**Quarterly is this organisation's and the instruments require no self-check at
all.** It is chosen against the dated conditions rather than as a rhythm: a
31 March report is seen three times before it falls due, and a 365-day
notification threshold is caught while there is still time to notify. Where an
instrument sets its own frequency for anything, **that frequency governs** and
this obligation does not replace it — the quarterly check confirms it happened,
it does not become it.

It must state **what to do when the answer is that a condition was not met.**
Several environmental compliance approvals require the holder to notify the
Director of a breach, and the notification duty does not wait for the quarter to
end. The procedure must say who decides, who calls, and that the register's "not
yet reported" option is a state with a deadline attached rather than a resting
place.
