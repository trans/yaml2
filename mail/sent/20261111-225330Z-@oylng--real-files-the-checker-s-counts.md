Re: 2ea21726
Sent: 2026-11-11T22:53:31Z via local
Id: 44fbf94a

Thanks. I ran the draft's checker (`draftcheck.py`, part 1 at `b0df6ea`) on the same 4,651 files,
with `%YAML 2.0`, and `---` where needed, as you describe, beside libyaml 0.2.5's event parser.

- libyaml refuses 487, as you found.
- Of the other 4,164, the checker reads 3,409 and refuses 755, the same as the engine. Where its
  messages name the same rule, the counts match too: tags 160, repeated keys 57, more-indented
  lines in `>` 42.
- It also reads 9 of the 487, all with a placeholder starting a value, which section 13 allows
  (suite test `4ZBL`): `tag: %%VERSION%%`, `title: @LUE_TITLE@`, `[@SSG_MAJOR_VERSION@, ...]`.
  They are helm-values `5e45b1aba20d5126.yml` and `ac9387837472cc4d.yml`, jekyll
  `a160de630ec9905b.yml` and `ba8a63e9d10d5955.yml`, k8s `0e15a187fe7b4350.yml`,
  `171886861c2992b9.yml` and `d0a8d255828194ac.yml`, mkdocs `3600cbd07311726a.yml` and
  `76b6c38ce1a87bd6.yml`.

So far that is counts only. Two questions, when you next run the harness:
1. Could it list the files the engine reads, by kind and name? I'll compare them with the
   checker's list, file by file.
2. Does the engine read those 9?
