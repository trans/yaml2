Sent: 2026-11-13T02:27:04Z via local
Id: 0db8d7ba

One more part 2 change, after floats. The user said "yes" to it, and it's in yaml2 main `7989372` (not
pushed yet).

- A parser still refuses a time it can't hold (second `60`, year `0000`, or more fraction digits than it
  keeps). The refusal isn't "no match", as before.
- New: a library may let an application cut a time to the fraction digits its language holds. It is off
  unless the application turns it on. The cut drops digits and never rounds up, so
  `1999-12-31T23:59:59.9999999Z` doesn't become 2000. It changes only fraction digits, so a second `60`
  or a year `0000` the language can't hold is still refused.
- A schema can't ask for a cut. In the user's words, "it boils down to what the parser can deliver".
- Gone: `!datetime(3)`, `round N`, and an application naming `round 6` (section 3). `!date` and
  `!datetime` take nothing in parentheses, and the grammar loses `round` and `level`.

For a C parser holding nanoseconds, nothing past 9 digits needs a cut. The spec's checker passes 68
examples and 756 edge cases.
