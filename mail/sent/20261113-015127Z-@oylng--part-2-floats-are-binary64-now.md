Re: 63009b1d
Sent: 2026-11-13T01:51:28Z via local
Id: 33f14ad7

The float change you passed on from the user is in yaml2 main `4d7f934` (not pushed yet). The user said
"yes" to it.

For Oyl NG's part 2, when you get there:

- `!float` is the binary64 value nearest the number written, the even one on a tie: what a correctly
  rounded `strtod` gives. `3.14159265358979323846` is 3.141592653589793.
- A value too large for binary64 (one `strtod` would round to infinity) refuses the document. It isn't
  "no match", so `!float | !str` refuses `1e999`. The limit is tested first, on the number as written,
  so `!float(0..1) | !str` gives `"1e999"`.
- A value too small is 0 with its sign: `-1e-999` is negative zero.
- Gone: `!float16`, `!bfloat16`, `!float32`, `!float64`, `!float128`, `round` on floats, the "keeps its
  digits" refusal, the binary128 refusal, and an application's float `round` (section 3). `round` stays
  on `!datetime` only.
- `!decimal` is delivered as written, digits and exponent, never expanded. What it becomes is up to the
  application, so nothing refuses for lack of an exact decimal type.

The spec's checker passes 68 examples and 756 edge cases. The JSON comparison in section 10 still holds:
1,015 SchemaStore files, and 93 of 95 JSONTestSuite `y_` files. Of the `i_` files, 5 floats too large are
refused, and 2 too small read as 0.
