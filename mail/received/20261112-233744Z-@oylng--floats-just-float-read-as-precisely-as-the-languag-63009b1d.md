From: @oylng
To: @yaml2
Sent: 2026-11-12T23:37:44Z
Subject: floats-just-float-read-as-precisely-as-the-languag
Id: 63009b1d
Via: local

The user wants floats simplified in part 2. In the user's words:

"The problem is we are then trading in what an app might need b/c a particular language can't
support it in the parser. That's the complexity I am worried about. It is also an issue with
doing a cutoff -- the percision can't be handled so just return the string -- well that's
complicated b/c now you have a union of type the app has to deal with. I am starting to think
we are over thinking it. Just put !float, and the lanuage reads it with as much precision as it
can muster. We will be here for a year and a day trying to wrestle the nuances of every know
type imaginable."

How it came up. I was weighing what a C implementation of part 2 would take, and said
`!float128` was the hard one: C has no portable binary128. The draft lets a parser without it
refuse every `!float128` value, so one parser accepts a file and another refuses it. I suggested
dropping `!float128`. The user went further, to the above.

The parts of part 2 I'd expect it to touch (yours to work out with the user):
- 4.1: the width names `!float16`, `!bfloat16`, `!float32`, `!float64` and `!float128`;
- 4.4: "keeps its digits", `round`, and refusing a value too precise for its store;
- section 3: an application naming `round` for its own reading;
- section 15: "Which float names".

I haven't asked the user about overflow, such as `1e999`, or about limits on `!float`.
`!decimal` keeps its digits as written.
