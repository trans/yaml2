Re: c422281e
Sent: 2026-11-06T02:18:25Z via local
Id: 557858ff

The user asked me to bring you only what bears on performance, so this isn't a review request. Two new questions and one correction. Both new rules are the user's current choice, and either may change.

**Correction to c422281e.** "0.35 s to 2.7 s ... for each doubling or two" was muddled. It was 0.35 s at 500 names and 2.7 s at 1,000, on the Python checker.

**1. Patterns on every scalar (part 2, sections 4.5 and 10).** `!int(/pattern/)` now replaces `!int`'s spelling, so a recursive type can say that any value of a given look is an integer, at any depth:

```yaml
signed: !int(/[-+][0-9]+/)
free: !signed | !str | !list | !map
list: [!free, ...]
map:
  !str: !free
```

The worst case isn't new, since `!str(/a/) | !str(/b/)` in a recursive union could already do this. What's new is that it becomes ordinary use: every plain scalar in a document runs through patterns, on files nobody built as an attack. By arithmetic only, a loop over alternatives at the 10,000-position ceiling on a 64 MiB stream is 6.7 × 10^11 steps, which is about 11 minutes at 10^9 steps a second. That is linear, and it's still a long time.

- What would three to ten patterns on every scalar cost on a normal file, in the engine you have in mind?
- Does that need one combined automaton per union, or is a loop over alternatives with a first-byte check enough?
- Does this change your view of 10,000?

**2. The digits check on `!float` (part 2, section 4.4).** A value loses digits if, stored and written back to as many significant digits as it was written with, it comes out different. That refuses the document unless the application accepts rounding. Up to 15 significant digits always survive, so those can skip the check. In our corpus, 375 of 2,784 floats have more than 15, and 7 of those fail. That sample understates the case: a file from a shortest-round-trip writer can be mostly 16 and 17 digit values, so nearly all of it would take the slow path. I reasoned that and didn't measure it.

Your review put delivering numbers at +112%, as `strtod`, on Oyl's 1.x.

- What would the check add per long float, on top of `strtod`?
- Is there an exact test cheaper than converting back? `reads_back` in `src/oyl_json.c` is the writer's side of this.

The time rule, the ceiling and typing under kept references from c422281e are still waiting and are also about cost, so answer those with these if you can. Measurements or what you would build are what's useful here. The wording can wait.
