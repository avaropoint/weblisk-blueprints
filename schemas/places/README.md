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
