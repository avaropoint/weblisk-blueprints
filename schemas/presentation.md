# Schema: Presentation

How an organisation's own look, its export layouts and the way it files its
repositories are held in the tenant, so that every client presents and files
its content the same way, and none of them holds it.

Three files, each an entry of the organisation's own repositories, written by
a person and read by any client:

| file | holds |
|---|---|
| `presentation/theme.json` | the organisation's theme: the values it gives the tokens a client renders with |
| `presentation/exports/<id>.json` | one export layout: how a document is laid out when it is rendered for print or for a signature |
| `presentation/filing.json` | the organisation's categories, what each lets a client do with the repositories filed in it, and which repositories are filed in each |

None of them is read by a tenant service. A client reads them, and that is the
whole of their use: they are here because they are the customer's, and two
clients holding their own copies would disagree with no way to settle it.

---

## Why it is content

A theme, a layout and a filing are authored by a person, changed over time,
and answer for nobody but the organisation, which is what content holds
([`architecture/content`](../architecture/content.md#overview)). Held as
entries they are text a plain editor can read, every change to them is one
change in the repository's change log, and a tenant rebuilt from its
repositories has them back without a store of their own
([`architecture/tenancy`](../architecture/tenancy.md#what-a-tenant-is-rebuilt-from)).
A record store would have held the same values where only a running service
could read them, and a client's copy is not the tenant's at all.

**Documents are never presented on disk.** A theme applies to a client's own
screens and to what it renders — an export, a signing page — and never to the
bytes of an entry. Rewriting a document to carry a look would change its
digest, which every signature over it is made against
([`patterns/content-identity`](../patterns/content-identity.md)).

---

## Where each file lives

**In a repository declared at the organisation's `scope_path`**, at the path
the table above gives. A project that needs its own keeps the same path in a
repository declared at the project's `scope_path`, and its file applies to that
project alone, as a project refines a programme it inherits
([`schemas/programme`](programme.md#one-act-by-a-person-at-the-organisation)).
`presentation/filing.json` is the organisation's alone: a project files
nothing of its own.

**One at a scope.** A client writing one looks for it in every repository at
that `scope_path` first, and writes there if it finds it. Where it finds the
same path in two repositories at one `scope_path`, it reports both, by
repository id and path, and applies neither, because choosing one would decide
which of two authors' files governs without either of them.

**The organisation is the top.** No repository is held at the tenant alone
([`architecture/content`](../architecture/content.md#types), `scope_path`), so
there is no layer above the organisation's. Below the organisation's file,
where it has none, is the client's own default, which is the client's product
and not the tenant's.

---

## The theme

```json
{
  "name": "Example",
  "tokens": {
    "accent": "#1f6feb",
    "header-mark": "presentation/mark.svg"
  }
}
```

| key | required | holds |
|---|---|---|
| `name` | yes | what a person calls it |
| `tokens` | yes | token id to value, each value a string |

**The tokens are the client's.** Which tokens exist, what each controls and
what values each accepts are the rendering client's own declaration, a closed
set as capabilities are ([`schemas/kinds`](kinds.md#the-model-open-kinds-closed-capabilities)):
a token nothing renders would look like configuration and do nothing. A token
the client does not declare is reported, by id, and not applied; a value the
client refuses — one failing the contrast its own themes pass, one moving
colour where its grammar forbids — is reported, naming the token, and not
applied. Neither is dropped from the file: it is the organisation's, and a
second client may declare what the first does not.

**Layered token by token.** A client starts from its own defaults, sets every
token the organisation's theme gives, then every token the project's gives,
so a project's file need name only what differs.

---

## Export layouts

One file per layout, at `presentation/exports/<id>.json`, `<id>` kebab-case
and the layout's identity.

```json
{
  "name": "Controlled copy",
  "description": "Number, revision and effective date on every page",
  "order": 1,
  "layout": {}
}
```

| key | required | holds |
|---|---|---|
| `name` | yes | what a person picks it by |
| `description` | no | what it is for |
| `order` | no | where it sits among the organisation's layouts, ascending |
| `layout` | yes | the layout itself: which sections are rendered, page size and orientation, what each header and footer slot carries, and the mark |

**The layout's keys are the rendering client's**, as a theme's tokens are,
and a key it does not render is reported and left in the file. A project's
file with the same `<id>` replaces the organisation's for that project, whole,
and a project's file with a new `<id>` adds a layout there alone. An
organisation with no layouts exports with the client's own.

---

## Filing

```json
{
  "categories": [
    {
      "id": "drawings",
      "name": "Drawings",
      "description": "Plans and submittals",
      "order": 1,
      "capabilities": ["asset-library"],
      "repositories": [{"scope_path": "example/head-office/site-a", "id": "drawings"}]
    }
  ]
}
```

| key | required | holds |
|---|---|---|
| `categories[].id` | yes | the category's identity, kebab-case, unique in the file |
| `categories[].name` | yes | what a person sees |
| `categories[].description` | no | what is filed in it |
| `categories[].order` | no | where it sits, ascending |
| `categories[].capabilities` | yes | what a client may do with a repository filed in it. Empty is allowed and means nothing |
| `categories[].repositories` | yes | each repository filed in it, by `scope_path` and `id`, as the content service declares it ([`architecture/content`](../architecture/content.md#types)), never by a path or a locator |

**The categories are the customer's; the capabilities are not.** A category
is any word the organisation files by, as many as it likes. A capability is
one the reading client implements, a closed set as kinds' capabilities are
([`schemas/kinds`](kinds.md#the-model-open-kinds-closed-capabilities)), and
one it does not implement is reported and grants nothing. A repository is
named by its `scope_path` and its `id` because its `id` is unique only within
its `scope_path`, and both survive a re-placement
([`architecture/content`](../architecture/content.md#types)).

**Unfiled is a real answer.** A repository in no category has no capability a
category gives, and a client says it is unfiled; it is never given a default
category or a default capability.

**What a filing does not decide.** It decides what a client does with a
repository it reads. It decides nothing the tenant's services do: which
repository is a records repository, its custody and its ceiling are content's
([`architecture/content`](../architecture/content.md#the-custody-model)), and
which documents count toward a control is the kinds' and the person's who
confirms a relationship ([`schemas/kinds`](kinds.md#capabilities)).

---

## Who changes them, and how a client reads them

**A person changes them**, as any entry changes: directly, with
`content:write`, or by proposal, with `content:propose` and a person's
`content:decide` ([`architecture/content`](../architecture/content.md#who-may-move-an-entry)).
A client writes one only on a person's act. Nothing is written when a client
connects, starts or finds none, and an organisation with none is shown its
client's defaults, said to be the client's.

**The change log is the record.** Each change is one entry of the
repository's change log, naming who made it ([`architecture/content`](../architecture/content.md#the-change-log)),
and no client keeps a second record of what a theme, a layout or a filing
was.

**A client reads them through content**, with `content:read`
([`architecture/content`](../architecture/content.md#read-flow)), on the
person's own pass, and reads them again when the entry's digest changes. A
copy it keeps to render quickly is a cache, rebuilt from the entry and never
shown as the organisation's when the entry cannot be read.

**They count for nothing.** None of the three is a policy, a standard or
evidence, and a client classifies them as the [classification](kinds.md#classification)
does, which places them in no evidence chain.

---

## Known gaps

**No layer above the organisation.** A look or a filing meant for every
organisation of a tenant is written to each, because content holds no
repository at the tenant alone.

**The token and layout vocabularies are each client's.** Two clients that
declare different tokens or layout keys render one file differently, and each
reports what it does not render. Nothing in the corpus declares either
vocabulary yet.

**Integrations are not filed.** Filing names repositories. An integration a
client reads content through has no owner blueprint yet
([`protocol/types`](../protocol/types.md#capability), `integrations`), and so
no identity a filing could name.

---

## Verification Checklist

- [ ] A client reads a theme, a layout or a filing from the organisation's repositories, and a project's file at the same path applies to that project alone ([Where each file lives](#where-each-file-lives))
- [ ] Where one path is held by two repositories at one `scope_path`, a client reports both and applies neither ([Where each file lives](#where-each-file-lives))
- [ ] A token or a layout key the client does not declare, and a value it refuses, is reported by name and not applied, and the client does not remove it from the file ([The theme](#the-theme), [Export layouts](#export-layouts))
- [ ] A project's theme is applied token by token over its organisation's, and a project's layout with an organisation's `<id>` replaces it whole ([The theme](#the-theme), [Export layouts](#export-layouts))
- [ ] A filing names each repository by `scope_path` and `id`, never by a path or a locator ([Filing](#filing))
- [ ] A capability the client does not implement grants nothing and is reported, and an unfiled repository is given no category and no capability ([Filing](#filing))
- [ ] No client writes a presentation file except on a person's act, and none is written when a client connects or finds none ([Who changes them, and how a client reads them](#who-changes-them-and-how-a-client-reads-them))
- [ ] No entry's bytes are changed to present it ([Why it is content](#why-it-is-content))
