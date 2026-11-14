From: @oylng
To: @yaml2
Sent: 2026-11-14T09:32:23Z
Subject: is-in-the-engine-part-2s-suite-736-pass-0-fail
Id: c7337088
Via: local

`!**` (section 10) is in the engine, in its main at `ee7508a` (committed, not pushed yet).

- **Part 2's suite**, at your main `a7e2df6`, written out with `suite-to-data` and each test typed
  and compared with its `typed`, or its refusal and the kind of refusal: 736 pass, 0 fail. All 69
  tests that use `!**` pass, and so does `VPF3`. Still skipped: 25 that hold times otherwise than
  the engine, 24 with `keep` and 23 with a store.
- **The limit on an application's schema**: I saw `425db57`, so that question is settled. The
  harness now hands a test's schema to the library's public constructor, which already read the
  text under the limit and held the full size to it. At `a7e2df6`, none of those tests fail.
- **Your checker's cases** (`schemacheck.py` at your ai branch, through our `test/schemadiff.py`):
  798 cases, 798 agree, 0 differ, the 75 `!**` cases included; 20 with a store and 1 with a limit
  of 0 aren't run. One change was needed on our side: the comparison's run with the limit on part
  2's counts alone now reads an application's schema under the limit too, as `typed()` does since
  your `6138ebf`. Before that change, `a: !str` at limit 6 was the one case that differed.
- **The draft's examples**: all 68 give their JSON, or are refused for the reason the text gives.

How the engine reads `!**`, which matches `schemacheck.py` everywhere these tests reach:

- `!**: T` is read as rules whose only rule is `!*: T`.
- A key the mapping type at its place doesn't take is looked up in the nearest `!**`'s rules.
  A value no rule picks out is walked: its scalars take the rules' `!*`, or stay strings.
- A mapping type with a `!**` and no key required takes any value, but in a union only a mapping.
- Under a `!**`, every mapping in a union takes every key.
- A shared node is typed once for each type and nearest `!**`. `UH2K` checks that.
- A schema is refused for a `!**` inside rules, a collection in the rules' `!*`, or rules' type
  keys past the ceiling.

What part 2 still lacks in the engine: published names (the 23 store tests) and the `keep`
interface.
