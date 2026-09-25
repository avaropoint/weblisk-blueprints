---
id: it.asset-register
kind: register
title: IT Asset Register
structure: standard
path: registers/it-assets.md

satisfies:
  - iso_27001:A.5.9
  - iso_27001:A.7.9
  - nist_csf_2:ID.AM-01
  - nist_csf_2:ID.AM-02
  - can_ciosc_104:CIOSC-L1-14
  - cis_controls:1.1
  - cis_controls:2.1

register:
  title: IT Asset Register
  note: >
    One row per device, server, service or licence the organisation is
    responsible for. This is equipment and software; the information that lives
    on it is the information asset inventory in the security programme, and the
    two are deliberately separate because they have different owners and
    different lifecycles — a laptop is replaced and the information that was on
    it is not.

    An asset nobody can name an owner for is the one that never gets patched.
  columns:
    - {key: reference, label: Asset tag, type: text, required: true}
    - {key: type, label: Type, type: select, required: true,
       options: [Laptop, Desktop, Mobile, Tablet, Server, Network device, Printer,
                 Cloud service, Software licence, Removable media, Other]}
    - {key: description, label: Description, type: text, required: true}
    - {key: serial, label: Serial or identifier, type: text}
    - {key: assigned_to, label: Assigned to, type: user}
    - {key: owner, label: Owner (position), type: text, required: true}
    - {key: classification, label: Highest classification handled, type: select, required: true,
       options: [Public, Internal, Confidential, Restricted]}
    - {key: managed, label: Centrally managed, type: bool, required: true}
    - {key: encryption, label: Disk encryption enabled, type: bool, required: true}
    - {key: acquired_on, label: Acquired on, type: date}
    - {key: support_ends, label: Support or warranty ends, type: date}
    - {key: status, label: Status, type: select, required: true,
       options: [In use, In stock, In repair, Lost or stolen, Disposed]}
---

What this artifact must establish: everything the organisation is responsible
for keeping current, and who is responsible for each one.

It is the list that patching, endpoint compliance and disposal all count
against. A patch report that says 98 per cent compliant is a statement about the
machines the tool can see, and the machines it cannot see are exactly the ones
at risk — which is why the count of assets here and the count in the management
tool being different is a finding rather than a data quality issue.

`support_ends` is on the register because an asset past the end of its vendor
support is an unpatchable asset, and that is a risk with a date on it that can
be seen coming years ahead and almost never is.

`status: Lost or stolen` stays on the register rather than being deleted. A
device that left the building with information on it is a permanent fact about
an incident, and removing the row removes the only record of what was on it.
