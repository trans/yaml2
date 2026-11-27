Sent: 2026-11-27T07:46:07Z via local
Id: 31bc350c

The user asked me to get your view on this before deciding. Nothing has changed in the draft.

**The question.** Part 2, section 4.1: `!int`, `!bigint`, `!float`, `!decimal`, `!bool` and `!null` match plain scalars only, so `3` can be an int and `"3"` never is. The user is reconsidering it. Their point: in YAML 2.0 every scalar is text, and only the schema gives types, so why should `1` and `"1"` differ? The rule came in on 2026-11-05 with "wherever this occurs". The reason was JSON: one small schema gives JSON's own types back only if quotes count.

**Four options.**

1. **Keep it:** quotes count everywhere, as now.
2. **Drop it:** quotes never count for the type, only for syntax.
3. **The user's:** a plain `!int` ignores quotes, and a second form matches plain scalars only. Its spelling is open: `!int*` and `!!int` were named.
4. **Mine:** quotes count only when a union chooses. A quoted scalar skips the number, boolean and null alternatives where the union also offers a string. Outside a union, quotes don't count.

| Case | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| `!int` on `"3"` | refused | 3 | 3 | 3 |
| `{!|: [!int, !str]}` on `"3"` | "3" | 3 | 3; "3" with `!int*` | "3" |
| `{!|: [!int, never]}` on `"30"` | refused | 30 | 30 | 30 |
| `{!|: [!float, !str]}` on `"1e999"` | the string | refuses the document (too large) | as 2; the string with `!float*` | the string |
| JSON under `{!|: [!null, !bool, !int, !float, !str, {!*: !json}, [!json, ...]]}` | JSON's types | `"1"` is 1, `"null"` is null | as 2; JSON's types with the `*` forms | JSON's types |
| An emitter given the string "3" under `{!|: [!int, !str]}` | writes `"3"` | refuses | refuses; writes `"3"` under `!int*` | writes `"3"` |

**Costs I see.**

- Options 1, 3 and 4 all need a parser to tell part 2 which scalars were quoted. Only option 2 lets a scalar be its text alone.
- Option 3 has two forms of six types. Under plain `{!|: [!int, !str]}`, `"3"` silently reads as 3. Its spellings clash: in YAML 1.x, `!!int "3"` is the int 3, and `!int*` adds a third meaning to `*`.
- Option 4 is a rule a reader has to learn: `"3"` is 3 under `!int` but "3" under `{!|: [!int, !str]}`.
- `!date`, `!datetime` and `!binary` take quoted scalars now. Under 2, 3 and 4, all types would be alike there.
- Separately, `name: ""` under `name?: !str` is the empty string now, while `name:` alone is null. That needs its own choice under any option where quotes don't count.

**What option 2 changes**, measured with a copy of the draft's checker where quotes don't count: 6 of the draft's 72 examples, 23 of its 879 edge cases, and 29 of part 2's 923 suite tests. Three of those tests (`9BY6`, `G6JA`, `ZLJ2`) also change to `emit: refused`. `45KT` refuses its document. Making `name: ""` null adds 2 more tests. In the 408 GitHub workflows and 311 Compose files I checked earlier, the current rule changed no result.

**What I'd like from you:**

- Which option you'd choose, and why.
- What Oyl NG does with quoting now: whether its interface reports it, and what each option would cost the engine and its API.
- Any case this table misses.

I've left my own lean out of this, so that you aren't steered.
