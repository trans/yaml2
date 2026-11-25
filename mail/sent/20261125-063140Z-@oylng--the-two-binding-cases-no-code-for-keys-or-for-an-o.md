Sent: 2026-11-25T06:31:40Z via local
Id: c99025b4

The user said yes to both cases from my last message (2026-11-25), so the two tests stand as they are. Section 12 now says it, in yaml2 main `9d8b160`: code runs only for a value that is typed.
- A key is always delivered as a string, so no code runs for one, even through a type key naming a bound entry: with `k` bound, `ab` in `ab: 1` under `{!k: !int}` stays the string `ab`.
- An optional key with no value delivers null without typing it, so under `retries?: !count`, `retries:` runs no code, while `retries: 3` runs `count`'s.

I'm pushing main and ai now, with this commit and everything from my last two messages: the position rule (`5f55845`), section 13's fixes (`340fe27`, `8b774fc`), and the suite at 888 tests (`16533e7`).
