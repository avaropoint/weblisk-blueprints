---
id: isec.incident-response
kind: procedure
title: Security Incident Response
structure: procedure
path: procedures/security-incident-response.md

satisfies:
  - iso_27001:A.5.24
  - iso_27001:A.5.25
  - iso_27001:A.5.26
  - iso_27001:A.5.28
  - iso_27001:A.6.8
  - nist_csf_2:RS.MA-01
  - nist_csf_2:RS.MA-02
  - nist_csf_2:RS.AN-03
  - nist_csf_2:RS.MI-01
  - can_ciosc_104:CIOSC-L1-01
  - soc2:CC7.3

requires: [isec.policy]
template: security-incident-report

declares:
  obligation:
    id: isec.incident-investigation
    # Record-origin. An incident happens once, at a time; asking which month it
    # belongs to has no answer, so "investigate within five days of report"
    # cannot be a cadence.
    activity: Investigate a reported security incident and record what was found
    for:
      records: registers/security-incidents.md
      due: 5d after reported_on
      key: reference
    responsible: information-security-lead
    applies_to: the organisation
    records: registers/security-incident-investigations.md
    escalate: {after: 3d, to: senior-management}
    satisfies:
      - iso_27001:A.5.27
      - nist_csf_2:RS.AN-03
  register:
    title: Security Incident Investigation Record
    note: >
      One row per investigation, keyed by the incident's reference so the chain
      joins end to end. `root_cause` and `notification_required` are the two
      columns that cannot be left to prose: the first is what stops it
      happening again, and the second is what starts a statutory clock the
      organisation cannot restart later.
    layout: form
    review: required
    approvers: [information-security-lead]
    columns:
      - {key: reference, label: Incident, type: relation, required: true,
         target: /registers/security-incidents.md#records, display: reference}
      - {key: investigated_on, label: Investigated on, type: date, required: true}
      - {key: investigated_by, label: Investigated by, type: user, required: true}
      - {key: timeline, label: Timeline of events, type: longtext, required: true}
      - {key: immediate_cause, label: Immediate cause, type: longtext, required: true}
      - {key: root_cause, label: Underlying cause, type: longtext, required: true}
      - {key: data_affected, label: Information affected, type: longtext, required: true}
      - {key: notification_required, label: Notification required, type: select, required: true,
         options: [None, Individuals, Regulator, Individuals and regulator, Contractual only, Still being assessed]}
      - {key: notified_on, label: Notification made on, type: date}
      - {key: evidence_held, label: Evidence retained and where, type: longtext, required: true}
      - {key: actions, label: Actions arising, type: longtext, required: true}
---

What this document must establish for THIS organisation: how a suspected
security event gets reported, who decides whether it is an incident, and what
happens in the first hour.

It must give people one way to report and make it easier than not reporting. An
organisation with a security inbox nobody monitors has a reporting process that
works exactly as well as no process, and the people most likely to notice the
first phishing message are the least likely to know where the inbox is.

It must set severity criteria before an incident, not during one. The
classification decides who is woken up, and a scheme invented at 2 a.m. wakes
either everybody or nobody.

It must separate containment from investigation, and say plainly that
containment comes first and may destroy evidence. Where the organisation needs
the evidence — a suspected insider, anything that may be reported to police or
an insurer — it must say who decides to preserve rather than restore, and how.
A.5.28 is a control most organisations discover they needed after the disk was
reimaged.

It must name the external parties and the triggers for contacting them:
regulators, the insurer, the cyber centre, the bank, affected clients under
contract, and counsel. Where personal information is involved, the privacy
breach procedure runs alongside this one on its own statutory clock, and this
document must point at it rather than restate it — two documents describing one
notification duty is how the deadline gets missed twice.

It must require an underlying cause, not just an immediate one. "The user
clicked the link" explains the injury and predicts nothing; why the message
reached them, why the credential worked from a new country, and why nothing
alerted are the parts the organisation can act on.

Five days to investigate, escalating after three more. Long enough to involve
the people who do the work and short enough that the logs still exist — which,
for most organisations, is the real deadline nobody writes down.
