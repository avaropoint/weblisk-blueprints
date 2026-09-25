---
id: cenv.soil-destinations
kind: register
title: Register of Excess Soil Destinations
structure: standard
path: registers/soil-destinations.md

# A register carries no `satisfies:`. It records that a place was assessed; the
# duty to assess it belongs to the procedures that declare obligations over
# these rows, and a register citing a control could never be recorded as
# answering it.

requires: [cenv.policy]

register:
  title: Register of Excess Soil Destinations
  note: >
    One row per place this organisation sends excess soil to, or expects to.
    The register exists because the regulation asks two different questions
    about a destination and an organisation that keeps no list can answer
    neither: whether the place named in the filed notice is the place the load
    actually went to, and whether the place is lawfully able to receive it. A
    reuse site needs no approval of its own; a Class 1 or Class 2 soil
    management site, a transfer facility and a landfill are waste activities and
    need an environmental compliance approval under s. 27 of the Environmental
    Protection Act. A broker's assurance that a site "is approved" is not a
    record, and `approval_verified_on` is the column that turns it into one.
    Rows are not deleted when a site stops being used: a load that went there
    three years ago still has to resolve to a row, so `status` closes a site
    rather than removing it.
  columns:
    - {key: site_id, label: Destination reference, type: text, required: true}
    - {key: name, label: Site name, type: text, required: true}
    - {key: site_type, label: What the site is, type: select, required: true,
       options: ["Reuse site — final placement",
                 Class 1 soil management site,
                 Class 2 soil management site,
                 Local waste transfer facility,
                 Landfilling site or dump,
                 "Another project area under our control",
                 "Not yet determined"]}
    - {key: address, label: Location, type: text, required: true}
    - {key: operator, label: Owner or operator of the site, type: text, required: true}
    - {key: contact, label: Named contact who can acknowledge a load, type: text}
    - {key: approval_required, label: Approval the site needs, type: select, required: true,
       options: ["Environmental compliance approval — waste (EPA s. 27)",
                 "None — a reuse site receiving soil for final placement",
                 "None — a project area of our own",
                 "Not yet determined"]}
    - {key: approval_number, label: Approval or registration number, type: text}
    - {key: approval_verified_on, label: Approval seen and verified on, type: date}
    - {key: verified_by, label: Verified by, type: user}
    - {key: standards_table, label: Excess Soil Standards table the site accepts to, type: text}
    - {key: site_specific_standards, label: Site-specific standards apply, type: bool, required: true}
    - {key: reuse_site_notice_filed, label: Registry notice filed by the site under s. 19, type: select,
       options: ["Filed", "Not required — below 10,000 m3", "Not required — infrastructure undertaking",
                 "Not confirmed", "Not applicable"]}
    - {key: restrictions, label: What this site will not take, type: longtext}
    - {key: status, label: Status, type: select, required: true,
       options: [Approved for use, Under assessment, Suspended, "Closed — no longer used"]}
    - {key: approved_from, label: Approved for use from, type: date}
    - {key: approved_until, label: Approved for use until, type: date}
    - {key: note, label: Note, type: longtext}
---

What this artifact must establish for THIS organisation: every place its excess
soil goes, who operates it, and on what evidence somebody decided it was lawful
to send soil there.

It exists because **the destination is the half of the excess soil regime that
is not on our own site, and it is therefore the half nobody checks.** The
project leader's duties in O. Reg. 406/19 do not stop at the gate. Section 9
requires the destination information in the filed notice to be the information
for the actual location before soil is deposited there, which is a duty that can
only be discharged against a list. Section 22 forbids depositing reusable excess
soil at a landfill at all unless it is going to daily cover, roads, berms or
another ancillary use, or unless a qualified person has declared one of three
specific grounds — so "we sent it to the dump because it was cheapest" is not a
neutral commercial decision, it is a prohibition with a declaration attached.

**`approval_required` is a select with a real "none" and it is not a formality.**
A reuse site receiving soil for final placement is not a waste site and needs no
approval of its own; a soil management site, a transfer facility and a landfill
are waste activities under s. 27 of the *Environmental Protection Act* and cannot
lawfully operate without an environmental compliance approval. Getting this
backwards in either direction costs something: treating a reuse site as needing
an approval stalls a job for a document that does not exist, and treating a
soil management site as needing none is how soil ends up at an unapproved
receiving operation that the Ministry later closes, with this organisation's
loads inside it.

**`approval_verified_on` is the column an inspector reads.** The failure here is
never a decision to use an unapproved site; it is a number quoted by a broker on
the telephone, written into a notice, and never seen. A date and a person against
the verification is the difference between having checked and believing somebody.

**`status` closes a site, and rows are never deleted.** A destination that was
used and then withdrawn still has to exist, because the hauling records and the
Registry updates that cite it must resolve for at least seven years under s. 28.
A register that tidies itself up destroys the only route from a load to the place
it went.
