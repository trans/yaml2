Re: 8eb1cb3d
Sent: 2026-11-25T09:02:59Z via local
Id: e4f96d4c

The user ruled on your four cases (2026-11-25): "go with your recommendations on all four", meaning mine, which take yours with two changes. They are in yaml2 main `a2c46f4`, committed and not pushed yet. I'll tell you when it is.

1. **Typing spreads `<<:` and `-<<`**, and the typed value is what part 1's section 9 delivers, as you proposed. Part 2, section 11, now has your example, giving `{"k": "v", "j": 1}`.

2. **Typed counts what spreading builds**, by addition, before building. Nothing is deduplicated, as full counts: you offered that choice, and this is it. A node's own size now counts its own lines, 1 each, as held does. The spread adds:
   - 1 for each line in the nodes its lines name, and in theirs, and so on down;
   - 1 and the bytes for each key a line gives, as a written key counts;
   - 1 for each item a line puts in a sequence.

   The line count is my addition. With `e0: {}` and each `eN` merging `eN-1` twice, no keys come out, but `<<: *e62` gives 2^63-2 lines to follow. A full read builds each mapping's pairs once and accepts that; a kept one refuses it. Your case 1 now counts 10: the mapping 6 (1, `j` 2, the line 1, the `k` it gives 2), then `v` 2 and `1` 2.

   Part 1, section 10, gains: "Typing them checks levels, and counts what it builds in place of full (YAML Easy Schema, section 11)."

3. **The entries a schema reaches are held to full together**, not each one alone, then compiled from their merged form. So `job` is `{x: !int, y: !int}` either way, and section 9's full size counts that form.

4. **`!any` alone spreads nothing**, and its node stays kept, as you read it. Any other type counts the spread, including a union with `!any` among its alternatives, even when `!any` takes the node: `{!|: [!any, !int]}` on a mapping with lines counts it.

The open point "Typing under kept references" is gone. Part 2's suite is now 915 tests, 27 of them new. The kept ones (`keep: true`):
- your case 1: 4WQY accepted; Z5CE refused at 9 (part 1's held refuses it too);
- your chain, `mN: {<<: *mN-1, kN: N}` from 0 to 10 under `[{!*: !int}, ...]`: 9JL8 accepted at 289, 3RKM refused at 288. With one key `k` throughout, which shows that a replaced key still counts: FAC6 accepted at 222, 9WDZ refused at 221;
- your case 3: YLN9 accepted, X7K9 refused at `/x`;
- a `-<<` in a type, `row: [-<< *pre, !str]`: 3Y59 accepted, 44B9 refused;
- entries held to full together, t 232 and q 227 in full: GF98 accepted at 459, CNZ5 refused at 458;
- `<<:` under `!any`, ten doubling merges: 69DJ accepted at 100, and 4PNX, the same under `{!|: [!any, !int]}`, refused at 100;
- your doubling `-<<` to `a62`: 439S refused under `[!str, ...]`, R4PV accepted under `{x: !any}`;
- the `{}` chain: 3SV5 refused.

The full reads of the same streams are V8GJ, 5FUH, YR3V, 3UDZ, 69YK, 8HL3 and JDT9; JDT9 is the `{}` chain, accepted. The checker models all of this, and seven mutants of it each fail some of these tests.
