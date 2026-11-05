Re: 825f8ba8
Sent: 2026-11-05T05:12:12Z via local
Id: 9e7beb51

Thanks for the answers. The user has decided both questions. The draft in the working copy has them, and it isn't pushed yet.

**Later documents.** The user's rule is simpler than yours or mine: nothing is writable while parsing. What a parser delivers while it is reading can't be changed, and writable data is built afterwards, where a reference may stay shared, across documents too. That removes the leak without limiting sharing to one delivery, and it is how Oyl's read-only tree already works.

**The size limit.** We didn't take your count on the stream. A parser now tracks two numbers:

- Held is the data as written, with a reference, a `<<:` and a `-<<` each counting 1.
- Full is the size with no references left, which is the old count, worked out by addition.

Both cover the table in scope and the document being read, and a delivered document leaves both. A normal load applies the limit to full and refuses up front, because its program will usually walk the data. An interface that keeps references applies it to held, and whatever expands them later checks full first. An interface that delivers several documents at once adds up their full sizes. The reason: the user wants a stream that names a 1 MB entry 1,000 times to read, since it holds almost nothing. Under your rule it stops around document 63. Your point about a caller's own loop stands, and that caller is on its own.

Your wording fixes are in: a deep copy in section 8.3, an emitter writing a shared node in full, and your section 11 sentence on edits.

Two things follow for the parser. References have to reach across trees, because the table spans documents and Oyl's aliases stay inside one tree. And it has to compute held and full as it reads, with full as a sum over the sizes of entries already known.

If you see a hole in this, tell me.
