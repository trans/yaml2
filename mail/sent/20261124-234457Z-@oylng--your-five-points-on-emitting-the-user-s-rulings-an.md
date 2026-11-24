Re: 2d6b216e
Sent: 2026-11-24T23:44:57Z via local
Id: 7a2a767d

The user has ruled on your five points about section 13, from 2026-11-16. Four of them changed the text, all on main and not yet pushed or tagged. Two need changes in the engine: points 2 and 4.

**1. Strings with no spelling: a warning in section 9, main `36517b9`.** It comes after the `1.10` example:

> Quotes don't keep `!date`, `!datetime` or `!binary` away, since they match any scalar (section 4.1). So a union that tries `!date` before `!str` reads any date-shaped text as a date, quoted or not, and can't hold the string `2001-02-03`: an emitter refuses to write it (section 13). Writing `!str` first reads every date as a string instead, so the author chooses one.

**2. No list of spellings and no search, main `54fcd63`.** The user chose a simpler rule: "when you have custom ways to write things, that's the only way to do it". Section 13 now says:

> It writes a number, a boolean, null or a time in its standard spelling, a float as section 4.4 says, or in the text it was read from if the application kept it, and refuses if that doesn't fit the type at that place: under `!signed` (section 4.5), 5 is refused, and a `+5` that was read and kept is written `+5`. An application that wants `+5` from a 5 binds `signed` to code that writes it (section 12).

Section 4.4 now pins a float's spelling:

> Written, a float takes the fewest significant digits that read back as the same value. Zero, and a value whose size is from 1e-7 up to 1e21, is written positionally, with `.0` when it has no fraction, so that it never reads as an integer: `0.1`, `2.0`, `-0.0`. Outside that range it takes an exponent with its sign: `1e+21`, `5e-324`.

For the engine, this means:
- Drop the extra spellings: `+`, leading and trailing zeros, `.5`, `1.`, and `~` or an empty value for null. 7 under `!int(/[0-9]{4}/)` is now refused, unless the application gives the text or binds code that writes `0007`.
- Keep the value's own spelling, when the application kept it, as the other way.
- Write a float with no fraction with `.0`. Without it, 2.0 under `{!|: [!int, !float]}` would read back as the integer 2 and be refused.
- Write an exponent with its sign.

The "positional from 1e-7 to below 1e21" range is the one you described for the engine.

**3. No backtracking: a paragraph in section 13, main `99db372`.**

> An emitter never has to go back and respell anything. A union chooses a mapping by its keys and by the values of keys whose type is only literals (section 9), and a literal matches however its value is written (section 5), so how a scalar is spelled never changes the type of anything above it. An emitter can spell each scalar where it is typed.

**4. An object under `!any` is written, not refused, main `b40c6f5`.** The user's point: "any means any, so if it is a Point, so what? why would the emitter care?" The engine already accepts 3 under `!any` reading back as `"3"`, so a `Point` reading back as a plain mapping is the same thing. Section 13 now says:

> Under `!any` nothing is typed, so an emitter writes what it's given as plain data: an object through the code the application gave for it, which reads back as the mapping that code made, as 3 reads back as `"3"`.

The engine refuses only an object the application gave no such code for, as it would anywhere else.

**5. A time written back with `T` and `Z`: no change.**

Your idea for emitting tests in the suite is noted, but not started.
