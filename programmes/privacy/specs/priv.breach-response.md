---
id: priv.breach-response
kind: procedure
title: Privacy Breach Response
structure: procedure
path: procedures/privacy-breach-response.md

satisfies:
  - pipeda:PIPEDA-BR-1
  - pipeda:PIPEDA-BR-2
  - pipeda:PIPEDA-7
  - quebec_law25:BS-2
  - fippa_mfippa:FM-10
  - iso_27001:A.5.34
  - soc2:P6.1

requires: [priv.policy]
template: privacy-breach-assessment

declares:
  obligation:
    id: priv.breach-assessment
    # Record-origin. A breach happens once, and the assessment that decides
    # whether anybody must be told is due relative to its discovery — there is
    # no period a breach belongs to.
    activity: Assess a privacy breach for real risk of significant harm and notify if required
    for:
      records: registers/privacy-breaches.md
      due: 3d after discovered_on
      key: reference
    authority: PIPEDA s. 10.1 — report and notify as soon as feasible after determining that a breach has occurred
    interval_basis: required
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/privacy-breach-assessments.md
    escalate: {after: 48h, to: senior-management}
    satisfies:
      - pipeda:PIPEDA-BR-1
  register:
    title: Privacy Breach Assessment Record
    note: >
      One row per assessment, keyed by the breach reference. `harm_factors` is
      longtext and required because the statutory test is a judgement that has
      to be defensible: the Commissioner does not review the conclusion, it
      reviews the reasoning, and "assessed as low risk" with no factors recorded
      is a conclusion with nothing behind it.
    layout: form
    review: required
    approvers: [privacy-officer, senior-management]
    approval_order: sequential
    columns:
      - {key: reference, label: Breach, type: relation, required: true,
         target: /registers/privacy-breaches.md#records, display: reference}
      - {key: assessed_on, label: Assessed on, type: date, required: true}
      - {key: assessed_by, label: Assessed by, type: user, required: true}
      - {key: harm_factors, label: Sensitivity and probability of misuse — the reasoning, type: longtext, required: true}
      - {key: real_risk, label: Real risk of significant harm, type: select, required: true,
         options: [Yes, No, Cannot be determined — treated as yes]}
      - {key: individuals_notified, label: Individuals notified, type: select, required: true,
         options: [Not required, Directly, Indirectly — public notice, Not yet]}
      - {key: individuals_notified_on, label: Individuals notified on, type: date}
      - {key: regulator_notified, label: Regulator notified, type: select, required: true,
         options: [Not required, Privacy Commissioner of Canada, Information and Privacy Commissioner of Ontario,
                   Commission d'acces a l'information du Quebec, More than one, Not yet]}
      - {key: regulator_notified_on, label: Regulator notified on, type: date}
      - {key: third_parties_notified, label: Other organisations notified, type: longtext}
      - {key: containment, label: Containment and recovery, type: longtext, required: true}
      - {key: prevention, label: What is being changed to prevent recurrence, type: longtext, required: true}
---

What this document must establish for THIS organisation: who decides whether a
breach must be reported, on what test, and how quickly the decision is made.

It must state the test in the Act's own terms and then in the organisation's.
Under PIPEDA the trigger is a real risk of significant harm to an individual,
and the factors are the sensitivity of the information and the probability that
it has been or will be misused. Humiliation, damage to reputation or
relationships, identity theft, fraud, loss of employment or business
opportunities and financial loss are all significant harm — the test is not
limited to financial loss, which is the assumption that produces most wrong
answers.

It must require the reasoning to be written down, not the conclusion. The
assessment is reviewed after the fact by a regulator who cannot re-run the
judgement but can read whether one was made.

It must name every regulator that might have to be told and when, because an
Ontario organisation can owe more than one at once. The Privacy Commissioner of
Canada takes the PIPEDA report; a health information custodian reports to the
Information and Privacy Commissioner of Ontario under PHIPA on different and
lower triggers; an organisation with Quebec customers reports a confidentiality
incident to the Commission d'acces a l'information where there is a risk of
serious injury; and an institution's contractor notifies the institution, which
holds the FIPPA or MFIPPA duty itself.

It must cover notification to the individuals, including what the notice has to
contain: what happened, what information was involved, what the organisation is
doing, what the individual can do, and how to reach the organisation and the
Commissioner.

It must name who else is told — the insurer, the client whose data it was, the
police where there is criminality, and the payment brands where card data is
involved. Contractual notification deadlines are often shorter than statutory
ones, and the supplier register is where those commitments are recorded.

Three days for the assessment, escalating after forty-eight hours more. The Act
says as soon as feasible and sets no number, which is why the basis is recorded
as required and the interval as the organisation's working deadline against it.
