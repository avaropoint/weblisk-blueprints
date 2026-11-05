# Places

[`iso-3166.json`](iso-3166.json) is the list of places this corpus may name:
ISO 3166-1 alpha-2 country codes, ISO 3166-2 subdivision codes under their
country, and the one exceptionally reserved code [`schemas/standard`](../standard.md#applies_in--where-a-standard-has-force)
allows, `EU`. A standard's `applies_in` and an organisation's `operates_in`
([`architecture/orchestrator`](../../architecture/orchestrator.md)) are checked
against it, so a code that is well formed and assigned to nothing, such as
`ZZ`, is refused rather than accepted by its shape.

It is codes only, made from a named release of a named source, with the digest
of each file it was made from, all recorded in the file. ISO sells its own
machine-readable files and publishes no free one; the list says so, and a
newer ISO change reaches the corpus as a new release of this file, recorded in
its history, never as a silent difference. [`checks/places.py`](../../checks/places.py)
holds the list's shape and every standard's `applies_in` to it.

## Attribution and licence

The codes in [`iso-3166.json`](iso-3166.json) are taken from the
[iso-codes](https://salsa.debian.org/iso-codes-team/iso-codes) project, at the
release and commit the file's `source` names, from its
`data/iso_3166-1.json` and `data/iso_3166-2.json`. iso-codes publishes those
files under the GNU Lesser General Public License, version 2.1 or later
(LGPL-2.1-or-later), and that is the licence stated for the data here. Our
thanks to its maintainers, who track every change the ISO 3166 Maintenance
Agency publishes.

The file keeps the codes only: no country name, no subdivision name, no
translation and nothing else of those files. A country or subdivision code is
a fact that ISO 3166 itself assigns and publishes, not something iso-codes
made; iso-codes is where this corpus read those facts in a machine-readable
form, because ISO sells its own machine-readable files and publishes no free
one.
