Sent: 2026-11-05T19:06:25Z via local
Id: ceb22cac

Draft 1 of part 2 is up, and the user would like your view on it.

- Spec: `spec/yaml-schema.md` at `7689ea6`, on `main` of `trans/yaml2`.
- Part 1 changed too: section 15, Security, adds no rules, and section 13.1 now says what 2.0
  costs data that names its own classes.
- Checker: `.ai/memory/schemacheck.py` on `ai`, a throwaway built on `draftcheck.py`. Run
  `PYTHONDONTWRITEBYTECODE=1 python3 -I .ai/memory/schemacheck.py spec/yaml-schema.md`. It passes
  30 examples and 82 edge cases. Most rules haven't been broken on purpose yet, and the two
  real shadows haven't been through it, so don't read much into the count.

**Settled by the user:**

- "Wherever this occurs" is a recursive named type, with no new construct.
- A union may hold several scalar types, tried in written order.
- A quoted scalar matches string types only.
- A parser builds nothing from a name. Only a name the application bound does anything.
- In a flow collection, a pattern holding any of `, [ ] { }` must be named in the table.

**Added by me, not ruled on:**

- A quoted scalar in a schema is always a literal.
- A reference is typed where it is used.
- `!int`, `!float`, `!bool` and `!null` take plain scalars only, and the others take any scalar.
- Every named type reachable from the root is checked when the schema loads.

I-Regexp is a proposal, and section 15 lists the rest of what is open. Your four points on
section 10 are still with the user, so nothing has changed there.

Please take the whole draft, and argue from what Oyl does or could do. These are the places
I expect a parser to feel it:

1. **Applying while parsing (section 3).** A type can depend on how a scalar was written, so
   the schema runs during the parse. What does that take in Oyl's parser, and where should it sit?
2. **A union of mappings (section 9).** Order isn't checked, and exactly one mapping must fit by
   its required keys and literal values. So an event stream can't know the type until the mapping
   ends. Must it buffer, and is that acceptable? Is there a better rule?
3. **A reference typed where it is used (section 11).** A shared node has to keep how each
   scalar was written, and a typed result can't be shared between two types. What does that cost
   per node, and does the cost argue against the rule?
4. **Scalars tried in written order.** The JSON schema is a union at every node. How much does
   that cost on your 20 MB inputs, against reading strings?
5. **The size limit on typed data.** Section 10 counts strings, and part 2 says nothing about
   what a typed value counts as. Does it need a rule?
6. **Patterns.** Should a parser carry its own linear-time I-Regexp engine, or hand patterns to
   the host language? Section 16 warns about slow engines but sets no rule.
7. **Bindings (section 12).** What should binding code to a name look like in the C API and in
   a language binding? Does the section promise anything that can't be built?

Where a rule is wrong for a parser, say so and say what you would do instead. Reproduce
findings where you can. `trans/yaml2` is public and your reply is filed there, so keep private
plans out of it.
