# Internationalisation

**Reserved. Nothing here yet.**

`intl/` is for locale and spoken-language constructs: how content is authored,
selected and rendered for a locale, and what a tenant operating in several
languages needs from the platform.

## Why it is reserved before it is built

This framework serves organisations whose policies and procedures may exist in
several spoken languages, and it also has to talk constantly about programming
languages. One word cannot carry both without being qualified every time it is
used.

So `language` means a **programming** language, everywhere, unqualified — and
anything about spoken language or locale belongs here. Reserving the name costs
nothing now and removes an ambiguity that would otherwise have to be explained
in every document that touches either subject.

`intl` rather than `i18n` or `locale` because it is the word ECMA and ICU use,
so it reads correctly to anyone who has worked on this before.
