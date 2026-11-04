# Landscape: where YAML stands

*Updated 2026-11-04*

## The spec (checked 2026-11-03)

- Latest published: 1.2.2 (October 2021), no normative changes from 1.2.
- yaml/yaml-spec: `main` last changed 2023-05-23, `main-1.3` 2022-02-06
  (status: draft), `rfc-staging` 2021-09-20. No YAML 2.0 proposal there.
- yaml/YAML2 (2011) is an earlier 2.0 effort: a README, last pushed 2011-11-03, with
  issues from 2012 to 2021. Several are the user's and foreshadow rules here: #1 (type
  tags), #2 (a tagless YAML), #5 (front matter, literal plain scalars, flush-left
  strings), #6 (no `?`). So does yaml/yaml#4 (2014), which asks about a data document
  with a separate typed one of the same shape. The replies there: failsafe already
  allows it, and how a document binds to its schema doesn't belong in the document.
- yaml/yaml-test-suite is still maintained (last commit 2025-12-25).
- Open yaml-spec issues worth reading: #283 (choose features from usage
  data), #272 (security considerations), #33 (naming a schema in a file),
  #280 (drop `!!binary`), #286 (unreserve `@`), #337 (underscores in
  numbers).
- 1.2.2 section 6.8.1: `%YAML 2.0` "should be rejected" by a 1.2 processor,
  `%YAML 1.3` is read with a warning, and a document with no directive is
  assumed to be 1.2.

## What is deployed (@oyl's measurements, its ideas.md and dialects-design.md)

- Most YAML is written for libyaml-based loaders (PyYAML, Psych) or go-yaml
  v2 (`sigs.k8s.io/yaml`), which read YAML 1.1 types whatever the spec says.
- Same bytes, different data: of 5,742 local files, 104 (1.8%) held a plain
  scalar typed differently by PyYAML and 1.2 Core (2026-10-10). 88 of the 98
  booleans were `on` used as a key, 77 of them in GitHub workflows, where
  GitHub means the string. The rest: `NO` as a key, `1E-12`-style floats,
  timestamps, `<<`. docker-compose's `22:22` reads as 1342 in 1.1.
- Implementations disagree on syntax: libyaml accepts 15 of the test suite's
  94 invalid cases, in five kinds (2026-10-18). In practice this hardly
  shows: no real file PyYAML read was rejected by strict Oyl, across 10,553
  files.
- Version directives aren't portable: go-yaml v2 rejects `%YAML 1.2`
  (upgrade-design.md, decision 3), so a directive can't be the way a file
  says which reading it wants.
- Dates have no standard 1.2 spelling: the 1.2.0 change list dropped
  `!!timestamp`, with `!!binary`, `!!set`, `!!omap` and `!!pairs`.

## Feature use in local files (2026-11-03)

A walk over PyYAML's events: 3,363 unique files under `~/Projects` and
`~/.config`, skipping vendored directories and test corpora. Flow collections
in 12.7% of files, block scalars 10.4%, empty `key:` 2.1%, complex keys 0.48%,
multiple documents 0.15%, spelled nulls 0.15%, anchors 0.12%, tags 0.09%
(Ruby objects and a spec example), merge 0.06%.

These counts include 368 browser snapshots. Not a basis for cutting anchors or
merge. This is one person's code with
little Compose or GitLab CI in it, so those features are undercounted. A
public sample of those files would be needed.

## Separator characters in keys (2026-11-03)

The same walk without the browser snapshots, whose keys are full of URLs:
2,995 files, 111,461 keys. Keys holding `:` were in 1 file (1 key), `/` in 19
files (124 keys, mostly `app.kubernetes.io/name`-style), `.` in 160 files
(1,273 keys). No CloudFormation in the sample, so `Fn::Sub`-style keys don't
show up.

## Complex and duplicate keys (2026-11-03)

The same 2,995 files. Non-scalar keys were in 16 files, all of them Helm
templates where `{{ x }}` happens to parse as a flow mapping, so none were
meant. Duplicate keys were in 4 files, all test fixtures of bad input.

## What real JSON Schemas spend their keywords on (2026-11-03)

Five schemas: GitHub workflows, Compose, GitLab CI, package.json, Ansible
playbooks (2,399 schema nodes, 3,567 keyword uses). Counted by walking schema
positions, leaving out documentation keywords.

- Shape (`type`, `properties`, `items`, `required`, `$ref`, `enum`, ...): 86.2%.
- Unions and conditions (`oneOf`, `anyOf`, `allOf`, `if`, `not`): 7.8%.
- Validation (`pattern`, `minLength`, `minimum`, `format`, ...): 6.0%.

Per node: `$ref` is common (560 uses), so named types matter. 118 nodes are maps
with arbitrary keys. 68 unions mix a scalar with a sequence or mapping, which
shape can tell apart. All 117 unions of
scalar types include string (`boolean|string` 38, `integer|string` 33,
`number|string` 29, all three with string 17).

## YPATH so far (checked 2026-11-03)

No agreed standard exists. yaml/yaml-path is an empty repository. The others:
Peter Murphy's YPath proposal (v0.4, 2011), Ruby's old `YAML::YPath`, the
`yamlpath` Python tool, and andrewmd5/cyaml's YPATH 1.0. The last two are
query languages that return many nodes, and cyaml's steps don't cover keys
with special characters. JSON Pointer (RFC 6901) is the closest match for
naming one node.

## Where `<<` sits, and what it changes (2026-11-04)

4,192 unique files (the 311 public Compose files plus `~/Projects`), 32 with merge,
299 uses. 276 are the first key of their mapping. The 23 others are in 3 files: 11
each in two Compose files, no local key clashing with a merged one, and 1 in a test
fixture, `oyl.go/testdata/anchors.yaml`. No mapping has two.

`{y: 3, name: a, <<: {x: 1, y: 2}}` with `<<` last gives `y: 3` in PyYAML 6.0.3 and
go-yaml v3.0.1, and `y: 2` in Psych 5.2.2, where the merge overwrites the local key.
The fixture does this for real: `worker`'s `restart` is `on-failure` in PyYAML and
`always` in Psych. With `<<` first all three agree on values. Key order differs when
`<<` isn't first: PyYAML keeps merged keys first (`x, y, name`) wherever `<<` is
written, Psych puts them where `<<` is. Go's map print sorts, so it shows no order.

Same sample: 92 of the 299 mappings override a merged key. `<<: *base` (x, y),
`name: a`, `y: 3` gives `x, y, name` in PyYAML and Psych, as do Python `{**b}`, Ruby
`Hash#merge` and JS spread. Putting overrides where they are written instead would
change the order of 91 of the 299, in 17 files.

More than one merge, with a (p, q) and b (q, r). `<<: [*a, *b]` gives q from a in
PyYAML, Psych and go-yaml v3. Their keys come out `q, r, p` in PyYAML and Psych, the
sources reversed. Two `<<` lines give q from b in PyYAML and Psych, the opposite
winner, and an error in go-yaml v3. Same sample: 260 of the 299 uses name one source,
39 are lists, in 5 files, 33 of them with two or more sources. Their 78 sources are
77 references and one inline mapping, in the `oyl.go` fixture. No list has a key in
two sources, a thin sample for "who wins". No mapping has two `<<` lines, which says
little, as 1.x forbids duplicate keys. With no list, the two-line result (`p, q` from
b, `r`) is also what JS spread, Ruby `Hash#merge` and Python `{**a, **b}` give.

Is `<<` ever data? In 4,347 unique files (the same sample plus `~/.config`): no quoted
`"<<"` key, no plain key starting `<< `, and one plain value starting `<< `,
CircleCI's `<< parameters.executor >>`. Quoted `"<<"` is a literal key in PyYAML and
go-yaml v3, but Psych merges it: `{"<<": {"a": 1}, "b": 2}` gives `{a, b}`.

### With GitLab CI added (2026-11-04)

The counts above are Compose and local files, and undercount this. In 369 public
`.gitlab-ci.yml` files, 55 use merge, 483 uses: 278 first and 205 late, in 19 files,
usually after `dependencies`, `needs` or `stage`. None of the 205 has a local key
clashing with a merged one, so moving `<<` first changes no values. No list form at
all. 39 mappings, in 4 files, have two `<<` lines, always together, and 4 of those,
in 1 file, have a key in both sources; GitLab reads with Psych, so the later wins,
which is the 2.0 rule. So 782 uses in all: 554 first, 228 late, and only the `oyl.go`
fixture clashes.

Flow: none of the 782 uses is in `{ }`, and none of the 57 `- *x` uses in GitLab with
x a sequence is in `[ ]`. All three parsers accept `{<<: *a, x: 1}` and `[<<: *a, x]`,
and Psych's late-merge difference shows in flow too.

## Sequence merge (2026-11-04)

An old request, refused because `<<` was a string key and new syntax would touch
plain scalars, neither of which binds a clean break. yaml/yaml-spec#28 (2018, closed
2021) proposed `-<<` itself. yaml/yaml#35 (2017, closed) proposed `<< *x`. yaml/yaml#48
(2019, open, 45 comments) carries it on, with `<`, `+` and `-*x` among the spellings.
The discussion there ends up at concatenation, not set union.

Reuse of a list inside a list: 18 of 369 public `.gitlab-ci.yml` files (a search
sample, not random): `!reference` 66 uses in 10 files, `- *x` with x a sequence 57
uses in 8. None in the 311 Compose files or the 3,975 local files. GitLab flattens
these itself; its docs allow `!reference` nested 10 levels in `script`, and their
example builds lists from lists. 55 of the 369 use `<<`. No scalar in any of these
files starts `-<<`.

## How far references expand (2026-11-04)

Measured with [growth.py](growth.py): 4,656 unique files, 118 with references (GitLab
74, Compose 39, local 5). Expanded size over written size: median 1.32, 99% 8.71, max
11.64, a GitLab file. `cost <= 20 * written` holds at every reference in every file.
Few files at the high end, and search samples, so this is a guide.

Parsers today, on a 3,000-key entry used 3,000 times. A 47 KB file of `- *a`: PyYAML
and Psych load it at 17 MB peak, every item the same object. A 59 KB file of
`- <<: *a`: PyYAML 391 MB, Psych 306 MB, since each merge copies the key list.
go-yaml v3 refuses both, "excessive aliasing". So whether a file loads depends on the
parser, and sharing nodes doesn't cover merges.

A ratio of 100 (`growth.py --check 100 FILE`), dropped: the 1 MB, 500 KB entry,
100,000 `- *a` file is refused at reference 101, 30 levels of doubling in 667 bytes at
reference 20. But it has no ceiling.

A total of 64 MiB (`growth.py --total 67108864 FILE`): the 1 MB file is refused at
reference 134, the doubling file at 45, the 59 KB merge file at 2,930 of 3,000. That
last one is the worst case near this limit: 391 MB in PyYAML run in full. About 40 KB
is enough to reach it. Largest real total in the 4,656 files: 233,872, median 988.
Nothing large in these samples; generated files elsewhere may be, not measured.

GitLab list reuse: 38 of the 123 uses, in 10 of the 18 files, sit inside a definition
(a `.hidden` job or an anchored node), so a table ban on `-<<` would cost those files.

## Block strings and text documents (2026-11-04)

In PyYAML and Psych: `a: |` with `text` gives `text\n` if the file ends in a newline
and `text` if not. Blank lines after a `|` are dropped; after a `|+` they are content,
so a blank line between keys changes the value. A flush-left `--- |` string is refused
by both, though 1.2 allows it (spec example 9.3), and the test suite tags that example
`1.3-err`. Of 474 Markdown files with front matter under `~/Projects`, 27 (5.7%) have
a `---` line in the body, which would end such a document.

Multi-line plain scalars: in 40 of 369 GitLab files and 4 of 311 Compose files. The
GitLab ones sampled are mostly shell commands that rely on folding into one line
(`docker build` / `--pull` / ...). Measured with [syntax.py](syntax.py).

## Partial fixes so far

- KYAML (Kubernetes, KEP-5295): a subset with double-quoted value strings,
  printed by `kubectl -o kyaml`. Output only; input is still any YAML.
  Sources disagree on which release made it stable, so check before citing.
- Fixers: yamllint flags, `oyl_upgrade` rewrites in place, others re-emit
  the file (survey in @oyl's upgrade-design.md).
- Still to review: StrictYAML and other restricted subsets.
