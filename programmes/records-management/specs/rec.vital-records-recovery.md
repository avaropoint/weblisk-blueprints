---
id: rec.vital-records-recovery
kind: procedure
title: Retrieving Vital Records
structure: procedure
path: procedures/vital-records-retrieval.md

satisfies:
  - iso_22301:8.3
  - iso_22301:8.4
  - iso_27001:A.5.29
  - iso_9001:7.5

requires: [rec.vital-records]

# One sheet per vital record class, filled in by the person who knows where the
# thing actually is. Without it the first retrieval begins with somebody
# reconstructing from memory which lawyer holds the minute book — which is the
# question, asked on the worst possible day.
template: vital-record-recovery-sheet
---

What this document must establish for THIS organisation: how a vital record is
actually got back when the usual way of reaching it is gone.

The vital records standard says **which** records the business could not be
reconstructed without and where the copies are meant to be. This says **how one
is retrieved**, and it is a different document because it is read in different
circumstances — by somebody who may not be the records manager, possibly
without the office, the file server, the password manager, or the person who
set it all up.

It must be usable without the systems it describes. A retrieval procedure held
only in the document management system it tells you how to recover is the
canonical failure here, and it is common. Say where the printed or offline copy
is kept and who has one.

It must name, for each class, **the person or organisation the record is
obtained from and how they will verify who is asking**. A registrar, a lawyer, a
bank or an accountant will not hand over a minute book or a signing authority to
a voice on the telephone, and the identification they will accept is a fact
worth knowing before it is needed rather than during.

It must say what each record can be **opened with**. A protected copy in a
format nothing current can read, or an archive whose decryption key is held by
one person who has left, is a record the organisation believes it has. Name the
software, the version, the licence and the key holder — by position.

It must state the **order**. Some records unlock the others: the credentials
and recovery keys come first, because without them nothing else can be reached,
and the continuity plan's priorities decide the rest.

It must be **tested by retrieval, not by inspection**. The annual verification
in the vital records standard counts classes actually retrieved in a test for
exactly this reason, and this procedure is what a test follows. A test that
confirms the backup exists has confirmed the index.

It must say what is done with a retrieved copy afterwards — where it is held,
who has it, and how it is destroyed or returned. A vital record retrieved in an
emergency and left on somebody's laptop is now a vital record in a place the
schedule does not know about.
