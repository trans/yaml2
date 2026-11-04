# The rules of YAML 2.0

*Updated 2026-11-03*

The design, rule by rule, as the user sets them. Keep the user's wording for
each rule, and keep what the agent derived from it marked as such until the
user confirms it.

**Clean break.** The user chose this on 2026-11-03, over a subset that today's
parsers could read. YAML 2.0 need not be readable by existing parsers.

**The aim.** The user, 2026-11-03: simplify YAML as much as we can. The app
then interprets the data as it sees fit, or a YAML Schema types it.

## Rule 1: all scalars are just strings

The user, 2026-11-03.

Confirmed by the user, 2026-11-03: types come from the app or a YAML Schema,
never from the document.

Tags: the user doubts they're needed, since the schema handles typing
(2026-11-03). Out unless a need turns up. `%TAG` goes with them. Apps that
use tags as syntax (CloudFormation `!Ref`, GitLab `!reference`, Home
Assistant `!include`) would have to use ordinary mappings instead.

Follows from it (the agent's reading, not yet confirmed):

- No implicit typing. `no`, `on`, `0755`, `22:22`, `1E-12`, `2001-12-14`,
  `~` and `null` are all text.
- Quoting doesn't change the value: `42`, `"42"` and `'42'` are the same
  string. Quotes only decide which characters can be written.
- Scalar keys compare as strings: `1` and `"1"` are the same key.
- The data model so far: string, sequence, mapping.
- Cost: JSON stops being a subset in meaning. `{"a": 1}` still parses, but
  the value is the string `1`, and a JSON to YAML 2.0 to JSON round trip
  loses types unless something supplies them.

Probably, the user said on 2026-11-03: `key:` is the empty string, and the app
or schema decides what that means. Watch for whether a null value turns out
to be needed.

## Reuse: merge, and maybe no anchors

**Merge stays**, as far as the user can see (2026-11-03): it has proven too
useful to remove. The user's view is that YAML 1.2 dropping it is probably
part of why nobody has fully adopted 1.2.

**Anchors may go** (the user's idea, 2026-11-03, not decided): a workable
YPATH could replace them. Every node already has an address, so `&name` is a
second naming system.

The agent's proposal, not yet answered:

- `<<` can't stay a magic key. In 1.1 it's an implicit type, which Rule 1
  ends, so it becomes an indicator like `-`, and `"<<"` is the literal key.
- Keep `*` as the reference indicator, followed by a path from the root:
  `<<: *defaults`, `image: *versions/app`. The common case is then today's
  file with `&defaults` deleted, and Rule 1 holds because `*` can't start a
  plain scalar.
- Separate two things. A reference names exactly one node. A query (YPATH
  proper: wildcards, filters, many nodes) is for tools, and is a later
  question.
- Keys only in references, no sequence indices. `*steps/0` still resolves
  after someone inserts a step, to the wrong one: silent wrong data, a new
  mine. A renamed key fails loudly. So anything reused sits under a key.
- A reference is a copy of a finished node, so the data stays a tree. Either
  direction below rules out cycles: pointing at an ancestor is an error.
- Billion laughs survives. Nested copies still double, even with merge alone,
  so the spec needs a mandatory limit on expanded size.

**Which direction references point. Open.** The user's framing, 2026-11-03:
backward means being able to reference anything on demand; forward means
knowing what to look for, but filling in the data has to be queued until it
shows up.

The agent recommends backward only:

- The consumer never waits. Forward holds back everything after the first
  open reference, and a merge hides its mapping's keys until the target comes.
- A bad reference fails at its own line. Forward finds it at end of input,
  after the consumer may have acted on what came before.
- Define, then use, is how anchored files are already ordered, so the upgrade
  stays "delete `&name`".
- It can be loosened to allow forward references later without breaking any
  file. Tightening later would break files.
- Cost: anchors also told the parser what to keep, and dropping them gives
  that up. With the input in memory that costs nothing extra; on a pipe it
  means keeping the current document's bytes. A parser option refusing
  references would remove that for huge data documents.

## YAML Schema

The user's term, 2026-11-03: the optional layer that types the data. Nothing
is designed yet. Open: its own language or JSON Schema's vocabulary, and how
a document or app says which schema applies now that tags are out.
