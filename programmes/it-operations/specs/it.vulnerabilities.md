---
id: it.vulnerabilities
kind: register
title: Vulnerability Register
structure: standard
path: registers/vulnerabilities.md

satisfies:
  - iso_27001:A.8.8
  - cis_controls:7.1
  - nist_csf_2:ID.RA-01

register:
  title: Vulnerability Register
  note: >
    One row per vulnerability the organisation is aware of and has not yet
    fixed, on an asset it owns. Not one row per scan finding: the same missing
    patch on forty laptops is one row with forty in `affected`, and the same
    vulnerability found again next month is the same row, still open.

    `remediate_by` is the column everything turns on. It is calculated from the
    severity and the exposure by the rule the patching policy sets, entered when
    the row is opened, and never moved without an accepted exception — a
    deadline that can be edited quietly is not a deadline.

    `aware_on` is the date the organisation LEARNED, not the date the vendor
    published. The deadline runs from awareness, and backdating it to the
    advisory turns a fast response into a late one and a slow one into a crisis.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: title, label: What it is, type: text, required: true}
    - {key: identifier, label: CVE or vendor reference, type: text}
    - {key: asset, label: Asset or system, type: relation,
       target: /registers/it-assets.md#records, display: description}
    - {key: scope, label: Where it applies, type: longtext, required: true}
    - {key: affected, label: How many affected, type: int, required: true}
    - {key: severity, label: Severity, type: select, required: true,
       options: [Critical, High, Medium, Low]}
    - {key: exposure, label: Exposure, type: select, required: true,
       options: [Internet-facing, Reachable from the user network, Internal only,
                 Isolated or air-gapped]}
    - {key: exploited, label: Known exploited in the wild, type: bool, required: true}
    - {key: source, label: How it was found, type: select, required: true,
       options: [Automated scan, Vendor notice, Cyber Centre advisory, Supplier disclosure,
                 Penetration test, Reported by a person, Incident]}
    - {key: aware_on, label: Organisation became aware on, type: date, required: true}
    - {key: remediate_by, label: Remediate by, type: date, required: true}
    - {key: owner, label: Owning position, type: text, required: true}
    - {key: treatment, label: Intended treatment, type: select, required: true,
       options: [Patch, Configuration change, Compensating control, Replace or retire,
                 Accepted exception, Not yet decided]}
    - {key: exception_until, label: Accepted exception expires, type: date}
    - {key: exception_by, label: Exception accepted by (position), type: text}
    - {key: status, label: Status, type: select, required: true,
       options: [Open, In progress, Remediated, Accepted exception, Superseded, False positive]}
---

What this artifact must establish: what the organisation knows is wrong, on
which of its assets, and by when it has said it will be fixed.

The programme already counted `critical_overdue` in its monthly review. That
number had nothing behind it: there was no list of open vulnerabilities and no
deadline recorded against any of them, so "overdue" meant whatever the person
filling in the review believed on the day.

`exposure` sits beside `severity` because on its own a severity score is the
vendor's opinion about a laboratory. The same critical vulnerability on an
internet-facing gateway and on a laptop in a drawer are not the same piece of
work, and the deadline rule has to be able to say so.

`exploited` is a separate column, not a note. Known exploitation collapses every
other consideration and the register has to be sortable on it at three in the
afternoon.

`exception_until` and `exception_by` exist so an accepted risk is visible as
one. A vulnerability closed as "accepted" with no expiry and nobody's name on it
is not an accepted risk; it is a forgotten one, and it reads identically to a
fix on every report.
