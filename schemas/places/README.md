# Places

Two files are the list of places this corpus may name.
[`iso-3166.json`](iso-3166.json) holds the ISO 3166-1 alpha-2 country codes and
the one exceptionally reserved code [`schemas/standard`](../standard.md#applies_in--where-a-standard-has-force)
allows, `EU`. [`iso-3166-2.json`](iso-3166-2.json) holds the ISO 3166-2
subdivision codes, under their country. A standard's `applies_in` and an
organisation's `operates_in` ([`architecture/orchestrator`](../../architecture/orchestrator.md))
are checked against both, so a code that is well formed and assigned to
nothing, such as `ZZ`, is refused rather than accepted by its shape.

Each file is codes only, made from a named release of a named source, with the
digest of each file it was made from, all recorded in the file. ISO sells its
own machine-readable files and publishes no free one, and its Online Browsing
Platform's terms forbid scraping and automated extraction, so neither file is
read from ISO. A newer ISO change reaches the corpus as a new release of a
file, recorded in its history, never as a silent difference.
[`checks/places.py`](../../checks/places.py) holds both files' shape and every
standard's `applies_in` to them.

## Country codes: public domain

[`iso-3166.json`](iso-3166.json) was made on 2026-11-05 from IANA's
[Language Subtag Registry](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry)
(BCP 47, RFC 5646), at the `File-Date` its `source` names. The registry's
region subtags carry every ISO 3166-1 alpha-2 code, kept in step with the
ISO 3166 Maintenance Agency. IANA and the IETF Trust dedicate the protocol
registries to the public domain under the terms of CC0 1.0
([licensing terms](https://www.iana.org/help/licensing-terms), joint statement
of 10 November 2021), so the file carries no licence condition.

The method, recorded in the file's `source.method`: take every record of
`Type: region` whose `Subtag` is two letters, has no `Deprecated` field and is
not described as `Private use`; then remove the codes ISO 3166-1 exceptionally
reserves, which the registry carries as subtags but ISO assigns to no country
(`source.excluded`: AC, CP, CQ, DG, EA, EU, EZ, IC, TA, UN). `EU` comes back
as the one exceptionally reserved code `applies_in` may name. The result was
cross-checked against the UN Statistics Division's
[M49 overview](https://unstats.un.org/unsd/methodology/m49/overview/),
retrieved the same day: every one of its 248 ISO-alpha2 codes is in the file,
and the one code in the file M49 does not list is `TW`, which M49 does not
carry as a separate area. The 249 codes are the ones this corpus shipped
before; none was added or removed.

No request made to build it carried any personal data.

## Subdivision codes: LGPL, kept apart

[`iso-3166-2.json`](iso-3166-2.json) is still taken from the
[iso-codes](https://salsa.debian.org/iso-codes-team/iso-codes) project, at the
release and commit its `source` names, from its `data/iso_3166-2.json`.
iso-codes publishes that file under the GNU Lesser General Public License,
version 2.1 or later (LGPL-2.1-or-later), and that is the licence of the data
in [`iso-3166-2.json`](iso-3166-2.json), and of nothing else in this corpus.
Our thanks to its maintainers, who track every change the ISO 3166 Maintenance
Agency publishes.

The file keeps the codes only: no subdivision name, no translation and nothing
else of iso-codes' file. A subdivision code is a fact that ISO 3166 itself
assigns and publishes, not something iso-codes made; iso-codes is where this
corpus read those facts in a machine-readable form.

It stays apart because no public-domain or ISO-published source of ISO 3166-2
codes could be read lawfully and freely on 2026-11-05. Wikidata (CC0), measured
against this file that day, held 267 subdivision codes it does not, deleted
ones among them, and lacked 100 that it holds; a list that accepts deleted
codes refuses nothing it should. The file's `source.why_not_public_domain`
records that measurement. It is replaced when a source both free of copyleft
and faithful to ISO is chosen.
