---
id: cenv.environmental-approvals
kind: register
title: Register of Environmental Approvals and Registrations
structure: standard
path: registers/environmental-approvals.md

# A register carries no `satisfies:`. The duties to hold an approval, to meet
# its conditions and to renew it belong to the three procedures that declare
# obligations over these rows.

requires: [cenv.policy]

register:
  title: Register of Environmental Approvals and Registrations
  note: >
    One row per instrument that authorises something this organisation does to
    air, land or water — an environmental compliance approval, a registration in
    the Environmental Activity and Sector Registry, a permit to take water, a
    municipal sewer-use consent, a conservation authority permission. The rows
    are the subjects of two obligations: a quarterly check that the conditions
    are being met, and a renewal ninety days before expiry. Which means the
    register's boundary is load-bearing in both directions. Padding it with
    instruments this organisation does not hold — a receiving site's approval, an
    owner's permit — manufactures condition checks nobody owes; leaving out an
    EASR registration because "registration is not an approval" removes the
    instrument with the most onerous conditions in the set.
    `holder` exists because an approval held by the owner, and relied on by us,
    is a real and common arrangement that is not the same as holding one.
  columns:
    - {key: approval_id, label: Approval reference, type: text, required: true}
    - {key: instrument, label: Instrument, type: select, required: true,
       options: ["Environmental compliance approval — air, noise and vibration (EPA s. 9)",
                 "Environmental compliance approval — waste (EPA s. 27)",
                 "Environmental compliance approval — sewage works (OWRA s. 53)",
                 "Registration in the Environmental Activity and Sector Registry",
                 "Permit to take water (OWRA s. 34)",
                 "Municipal sewer-use consent or discharge agreement",
                 "Conservation authority permission",
                 Other]}
    - {key: number, label: Approval, registration or permit number, type: text}
    - {key: description, label: What it authorises, type: longtext, required: true}
    - {key: holder, label: Who holds it, type: select, required: true,
       options: ["This organisation",
                 "The owner, and we rely on it",
                 "A subcontractor, and we rely on it",
                 "The receiving site's operator",
                 "Not yet obtained"]}
    - {key: project, label: Construction project, type: relation,
       target: /registers/projects.md#records, display: project_id}
    - {key: site, label: Site or works it covers, type: text, required: true}
    - {key: applied_on, label: Applied for or registered on, type: date}
    - {key: issued_on, label: Issued or confirmed on, type: date}
    - {key: effective_from, label: In force from, type: date, required: true}
    - {key: expires_on, label: Expires on, type: date}
    - {key: no_expiry, label: The instrument has no expiry date, type: bool, required: true}
    - {key: conditions_summary, label: The conditions, in summary, type: longtext, required: true}
    - {key: monitoring_conditions, label: Monitoring and sampling the conditions require, type: longtext}
    - {key: reporting_conditions, label: Reporting the conditions require, and when, type: longtext}
    - {key: qualified_professional, label: Qualified professional who prepared the supporting reports, type: text}
    - {key: status, label: Status, type: select, required: true,
       options: ["In force",
                 "Applied for — not yet issued",
                 "Registered — conditions apply from the day of registration",
                 Expired,
                 Surrendered,
                 "Suspended or removed",
                 "Determined not to be required"]}
    - {key: documents, label: The instrument itself, type: attachment}
    - {key: note, label: Note, type: longtext}
---

What this artifact must establish for THIS organisation: every instrument that
makes an activity lawful, what each one actually requires, and when each one
stops.

It exists because **an approval is a document that arrives once and then governs
for years, and nothing about it recurs**. A permit in a drawer looks identical to
a permit whose annual report was never filed. The conditions in an environmental
compliance approval are imposed by the Director under s. 20.2 and they **become
the operative requirement**: the offence is not operating without an approval, it
is operating otherwise than in accordance with one, and the conditions are where
that happens. So the register records the conditions rather than the number, and
`monitoring_conditions` and `reporting_conditions` are separate fields because
they generate two different kinds of work.

**A registration in the Environmental Activity and Sector Registry belongs in
this register, and calling it "not an approval" is the mistake it exists to
prevent.** Under s. 20.21 a person may not engage in a prescribed activity unless
the activity is registered, the Director has provided a confirmation of
registration, the person engages in it in accordance with the regulations, and
the registration is neither suspended nor removed. It is not an application and
nobody assesses it — which is exactly why it is dangerous. The conditions in
O. Reg. 63/16 apply **from the day of registration**, and for construction
dewatering they include a water taking report and a discharge report each
prepared by a qualified professional **before** registration, an annual report of
daily volumes to the Director **on or before 31 March**, immediate notification
of any complaint relating to the natural environment, notice to the
municipalities and any conservation authority where the taking will run beyond
365 days, and five-year retention of the records. An organisation that registers
online in twenty minutes and files nothing for a year is in breach of an
instrument nobody ever posted to it.

**`no_expiry` is a required boolean because half of these instruments never
expire and the other half do.** An environmental compliance approval generally
runs until it is revoked or surrendered; a permit to take water is issued for a
term; an EASR registration persists while the activity does. A register with an
empty `expires_on` cannot tell "no expiry" from "nobody filled it in", and the
renewal obligation raises nothing for either. Asking the question makes the
silence answerable.

**`holder` is the column that stops this organisation relying on air.** Working
under the owner's permit to take water is lawful and ordinary; believing one
exists because the tender said so is not. A row whose holder is somebody else
still needs the instrument attached, because when a provincial officer asks to
see it on site, "the owner has it" is not production of a document.
