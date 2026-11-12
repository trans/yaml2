Sent: 2026-11-12T23:31:57Z via local
Id: 7b4dc24f

The user approved a change to part 1 today that asks something new of a parser. It is in yaml2's
main at `afbd21f`, which isn't pushed yet; your checkout of `../yaml2` has it.

Section 4.3: a document name may end in a fragment, `#` and then one or more ASCII letters, digits
and `=`. To a parser it is part of the name. A comment still needs a space or a tab before its
`#`, so `--- !a#b` is the name `a#b`, and `--- !a #b` is the name `a` and a comment. The grammar:

    name       ::= name-char+ ("#" frag-char+)?
    frag-char  ::= [A-Za-z0-9=]

Why: part 2 now names a published schema by its file and a PEP 503 hash, as pip's links do:
`tabcomputing.com/address/v1/address.yes#sha256=<64 hex digits>`. The address is `https://` and the
name before the `#`, and the root is the entry named like the file.

The suite has 6 new tests, 362 in all, tagged `name`:
- `YL2L` reads that published name, and `--- !a#b # a comment`;
- `3N37`, `L6H7`, `YVS5`, `T2DB` and `TE8G` refuse `--- !a#`, `--- !a#b#c`, `--- !a#b-c`,
  `--- !a#é` and `--- !#b`.

Nothing else in part 1 changed.
