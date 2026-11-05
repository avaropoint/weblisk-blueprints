---
family: schemas/instruction@1
version: 1.0.0
in: [repair]
---
# The form of an edit

The one form a repair's edits take, so that they can be applied to the file
as it stands without being interpreted.

## Why

A repair is applied by a tool, not read by a person: an exact span of the
current text, in whole lines, and what it becomes, refused where the span is
absent or occurs more than once
([`architecture/generation`](../architecture/generation.md#a-repair-is-an-edit-to-the-file-as-it-stands)).
A form described rather than shown is written differently by every model. A
repair of several files needs each answer to say which file it is for, and a
repair of one file must not, or its first line is read as an edit that is not
there.

## Text

```text
Answer for a file with edit blocks, one per change, each exactly in this
form, every marker on a line of its own:


<<<<<<< SEARCH

lines copied exactly from the current file

=======

the lines that replace them

>>>>>>> REPLACE


SEARCH holds whole lines copied exactly from the file's current content,
every space and tab included, and enough of them to occur exactly once.
REPLACE holds what those lines become; leave it empty to delete them. Blocks
apply in the order given, each to the file as the blocks before it left it.
Only if a file must change throughout, answer for it instead with the
complete corrected file, whose first character is the file's first
character. Write no explanation, commentary, preamble, summary or code fence.

When you may change one file, your answer is its edits alone. When you may
change more than one, precede each file's answer with its path on a line of
its own, in exactly this form: // filename: <path>. A file you do not answer
for is left as it is.
```
