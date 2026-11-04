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

## How the core team takes proposals (checked 2026-11-04)

- The written process is `rfc/ReadMe.md` on yaml-spec's `rfc-staging` branch: anyone may
  open a PR from the RFC template, filing an issue first "might make sense", and the
  core team (5 members on GitHub) reviews it. Future versions are meant to be several
  parts: grammar, test suite, guide, DOM, schemas, implementers' guide, change log.
- That process looks stalled: `rfc-staging` last changed 2021-09-20, and PR #85, which
  publishes the RFCs, has been open since 2021 with no team comment since. The 26 RFC
  files are mostly status new or 0. Public activity isn't the whole picture: the site
  says the team met weekly, and it has Slack and a mailing list.
- 1.3's stated aim (yaml.io/spec/1-3): "(mostly) _respecify_ YAML 1.2", "No significant
  features will be added", "Almost all production YAML should continue to work as-is".
  A clean break can't be 1.3. Major versions are free for one: 1.x processors should
  reject `%YAML 2.0`. Some RFCs target later 1.x versions, such as 1.5.
- AdaYaml, the 1.3 feature experiment, was archived on 2026-03-05. Its README says its
  ideas "have proven to be too difficult to propose" and calls it "the YAML 1.3 version
  that didn't come to be". Treat that as one signal, not a decision by the team.
- A search listing shows a 2026 Open Source Summit Europe talk on a YAML plugin system;
  the page itself wouldn't load, so this is unconfirmed. Look before presenting.
- Their RFCs already lean our way: unique anchors, no empty keys, a start marker on
  later documents and on top-level scalars, single-line top-level plain scalars, and
  visible indent on top-level literals. Cite them when presenting.

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

That sample understates `:`, because it held no GitLab files. Rechecked 2026-11-04 on
the 4,651 public files, 388,646 keys: a single `:` in 1,975 (1,438 of them Rails keys
like `:one`), `/` in 7,861, `.` in 7,584. So `:` is still the best separator, but GitLab
job names use it: 273 of 21,715 keys, in 42 of 369 files. Other real ones include
`aws:SecureTransport` and OAuth scopes like `read:accounts`.

Real paths exist only in GitLab's `!reference`: 126 in 369 files, 125 of them two
segments long. All 126 start at a hidden job. 21 hold a `:`, always in the first
segment (`[.deps:rocm, before_script]`). None holds a space.

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
`1.3-err`. Of about 475 Markdown files with front matter under `~/Projects`, 27 (5.7%) have
a `---` line in the body, which would end such a document, and 3 (0.6%) have a `...`
line. Pandoc already accepts `...` as the end of a metadata block; 2 of those files
close that way.

`...` in the public sample: 21 uses, 18 with nothing but comments or blanks after them,
3 followed by `---` on the next line and more documents, all in the Kubernetes sample.
No body of the 476 Markdown files starts with a `---` line. 1.2 allows a bare document
after `...` (spec example 9.3), but libyaml and pure PyYAML refuse one.

Multi-line plain scalars: in 40 of 369 GitLab files and 4 of 311 Compose files. The
GitLab ones sampled are mostly shell commands that rely on folding into one line
(`docker build` / `--pull` / ...). Measured with [syntax.py](syntax.py).

Block strings in the 4,026 public files: 4,213. `|` 2,810 uses, median 3 lines, 90% at
14, max 362. `|-` 302 uses, median 3, 90% at 29, max 594. `a: |text` is an error in all
parsers tested, so that spelling is free. Line-prefixed strings exist elsewhere: Zig's
`\\` and NestedText's `>`.

## Syntax use in public files (2026-11-04)

`syntax.py` on GitHub search samples of ten formats: Helm values, Kubernetes, Ansible,
OpenAPI, Rails locales, Jekyll, MkDocs, workflows, GitLab CI, Compose. 4,026 files
parsed; 474 didn't, mostly Helm templates. Not random samples, and libyaml's reading.

Share of files: flow 34.5, block scalars 23.2, `--- ` 19.2, `|` 16.8, `>` 8.3, `|-` and
`>-` 5.9, multi-line plain 4.7 (Ansible 17.9, GitLab 10.8), several documents 2.6
(Kubernetes 27.8), multi-line quoted 2.4 (Ansible 7.2), multi-line flow 1.6, `>` with
more-indented lines 1.4, trailing commas 0.8, `...` 0.45, tabs outside strings 0.25
(Jekyll 2.1), one-pair `[a: b]` 0.15, `- - x` 0.07, `|2` 0.05, BOM 0.05. `|+` has no
parsed use, and grep finds 1 in a file libyaml can't read. No UTF-16.

Escapes in double quotes are nearly all JSON's. The only others are `\ ` (213 uses, 9
files, the mark of an emitter wrapping lines) and `\_` (48 uses, 1 file).

Traps in the numbers. 37 whole-document scalars look like 0.9%, but those seen are
symlink targets and other files that aren't YAML. Locally 44% of files have multi-line
plain scalars, but 1,243 of those 1,256 are one generated dataset, so local shares
aren't used here.

Tabs split parsers: `key:\tvalue` loads in libyaml, Psych and go-yaml v3, and pure
Python PyYAML refuses it. `-\tvalue` is refused by all of them.

## How files say what they are (2026-11-04)

In the public samples, Kubernetes files carry `apiVersion` and `kind` (280 of 320),
OpenAPI files `openapi` or `swagger` (369 of 419), and 116 of 311 Compose files a
`version`. The rest say nothing: tools go by file name or path. The
`# yaml-language-server: $schema=` comment is in 8 of about 4,000 files, a root `$schema`
key in none. In the five JSON Schemas, `format` is 25 of 3,567 keyword uses: `uri-reference`
14, `uri` 7, `email` 2, `date-time` 1, `regex` 1.

Tag notation in the same 4,026 public files: no `tag:` URI written out, no `%TAG`. `!!`
appears in 153 files, 332 of its uses being `!!python/...`, as MkDocs configs use it.

## Partial fixes so far

- KYAML (Kubernetes, KEP-5295): a subset with double-quoted value strings,
  printed by `kubectl -o kyaml`. Output only; input is still any YAML.
  Sources disagree on which release made it stable, so check before citing.
- Fixers: yamllint flags, `oyl_upgrade` rewrites in place, others re-emit
  the file (survey in @oyl's upgrade-design.md).
- Still to review: StrictYAML and other restricted subsets.

## Patterns in real schemas (2026-11-04)

The user asked whether regex is needed at all, or whether PIC or glob would do.
[patterns.py](patterns.py) sorts every `pattern` value and `patternProperties` key in
all 1,015 SchemaStore schemas (downloaded 2026-11-04) by the simplest notation that can
write it. 494 schemas have patterns: 8,229 uses, 1,271 unique. Of those, 38 are plain
literals and 460 are enums with case spelled out (`[Aa][Ll][Ll]`, 6 schemas, mostly
generated). That leaves 773 that need a pattern, cumulatively:

| Notation | Unique | Cumulative |
|---|---|---|
| Glob: literals, `*`, `?` | 111 | 14.4% |
| PIC: fixed shape of digit, letter, any | 5 | 15.0% |
| Fixed shape with its own class (hex) | 34 | 19.4% |
| One sequence of class plus count (`[a-z0-9._-]+`) | 296 | 57.7% |
| Union of up to 8 such sequences (`8` is a choice) | 146 | 76.6% |
| Union of more | 15 | 78.5% |
| Repeated group, 79 of 107 a separated list (`x(,x)*`) | 107 | 92.4% |
| Lookaround or backreference, 29 of 31 a negative lookahead | 31 | 96.4% |
| Python's parser refuses (.NET named groups, `\p{..}`) | 24 | 99.5% |
| Other | 4 | 100% |

So PIC and glob fall short for one reason: neither can say one or more of these
characters, the commonest shape there is.

Dialects differ on small things, run here: `^abc$` matches `"abc\n"` in Python, not in
JavaScript; in Ruby it matches any line of `"x\nabc\ny"`; `\d` matches an Arabic digit
in Python, not in Ruby or JavaScript. 201 unique patterns use `\d`, `\w` or `\s`. 240
aren't anchored at both ends. Double-escaping is a real trap in YAML: in the 4,026
public files 2 of 57 unique patterns reach the app as `\\d`, which asks for a
backslash, so they can't match what they meant.

**I-Regexp (RFC 9485, 2023)** is an existing answer: a regex subset for interchange,
used by JSONPath (RFC 9535). It has literals, `.`, classes, counts, groups and `|`, and
`\p{..}`. It has no lookaround, backreferences, captures or `\d \w \s`. Section 5 maps
it onto ECMAScript, PCRE, RE2, Ruby and XSD, enveloped so the whole string must match.
In its grammar `^` and `$` are ordinary characters. Its security section says a
dedicated implementation can run in linear time, and existing engines may not.

## The draft against real files (2026-11-04)

[draftcheck.py](draftcheck.py) is a throwaway parser written from the grammar in
`spec/yaml-2.0.md`, not a reference. It passes all the draft's examples and its edge
cases; the size limit isn't implemented. Run on the 4,651 public files with `%YAML 2.0`
added, skipping files over 200 KB:

- PyYAML reads 4,164. The draft reads 3,544 of those as written, 85.1%.
- Every one of the other 620 traces to something decided: anchors 179, multi-line plain
  154 (by a rough heuristic), template text like `{{ x }}`, which is a mapping as a key,
  126, duplicate keys 59, more-indented lines in `>` 39, multi-line quoted 31, escapes
  10, `{a}` 8, tabs 7, block indicators 2, one-pair 1, and 4 others (a collection as a
  key, `!!python` tags, a file's own `%YAML 1.2`).
- Of the 3,544, compared with PyYAML reading all scalars as strings: 3,390 are identical,
  137 differ because a tag became text, and 17 because `|` always ends in one newline.

So the grammar reads real files as 1.x does, apart from what was cut on purpose.
Reading "as written" means all values are strings. It says nothing about what an app
does with them. `{ description: Queue full, or queue limit }` is a real bug the draft
catches: 1.x silently makes a second key with a null value.

## Comments that tools read, and forced quotes (2026-11-04)

Rough line scans of the 4,651 public files. About 54% hold a comment (some are `#` lines
inside block scalars). 158 files (3.4%) hold one a known tool reads: release tools 67,
`# noqa` 38, yamllint 24, helm-docs 16, kubeconform and the like 12,
`yaml-language-server` 8, security scanners 7, renovate 1.

1.x refuses a plain scalar starting with `%`, `@` or a backtick, so these have to be
quoted: 1,530 start with `%`, mostly Rails strings like `%{count}` and `%Y-%m-%d`, 26
with `@`, 9 with a backtick.

