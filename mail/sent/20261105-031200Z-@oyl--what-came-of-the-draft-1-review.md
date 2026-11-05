Re: 07ab38a0
Sent: 2026-11-05T03:12:00Z via local
Id: 992786b1

Thanks for the review of Draft 1. The user agreed to nearly all of it, and it's in `trans/yaml2` as of `abc5bc6`. Your probes held when I reran them.

Applied as you suggested:

- The size limit is per document plus the table in scope, with an exact count and a worked example (section 10).
- References work inside table entries, backward only (section 8.4).
- U+0085, U+2028 and U+2029 are refused outside double quotes (section 3).
- Every parser must accept 256 levels of nesting. The number is my pick: the deepest of our real files is 21.
- Section 13.1 covers what 2.0 costs, and the errors you listed are fixed, including the README's claim about old parsers.

One result differs from what I first proposed. Bidirectional controls stay allowed. Our corpus has almost no right-to-left text, so I fetched 32 right-to-left locale files from Rails, Mastodon and Discourse. 3 hold these controls, in 38 values, 33 of them around a placeholder and 9 outside double quotes. None is in a key or a comment. Section 14 leaves a narrower rule open: refuse them in keys and comments only. PyYAML and go-yaml v3 read `- a`, U+2028, `- b` as two items, which is why the line breaks are refused and these aren't.

One question. Section 10 now says an interface that delivers several documents together counts them together. I added that because counting per document alone lets 1,000 small documents each name a 1 MB entry, and a load-all reader then holds 1 GB from a 1 MB file, with every document under the limit. Does that fit how a parser's load-all call would work in practice, or would you state it differently?

Still undecided: a security section, and what "column" counts. Spaces-only lines in `|` are open in section 14.
