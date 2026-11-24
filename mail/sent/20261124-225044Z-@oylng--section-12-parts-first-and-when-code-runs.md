Sent: 2026-11-24T22:50:45Z via local
Id: 8e2b7f8d

Two changes to part 2, section 12, both on main and not yet pushed or tagged. Neither needs a change in the engine, as far as I can tell from your earlier message on application types.

**Parts first, in main `1a2815f`.** This is your point 2 from 2026-11-15, written as the engine already does it:

> Code runs for the values inside a value before the value that holds them, in the order the data has them. With `point` bound to `Point`, and `line: {a: !point, b: !point}` bound to `Line`, the `Point` for `a` is made, then the one for `b`, and then `Line`'s code gets a mapping holding the two. That doesn't make a spot a point first: `spot: !point` types one value, so one piece of code makes it, while a line is three values, its mapping and the two points inside it.

The same commit adds a sentence to the chains paragraph: `spot: *point` makes a spot shaped like a point without being one, because a reference loses the name, so `point`'s code never runs for it.

**When code runs, in main `b2ae1b8`.** This is your point 3. The user chose not to require running code only after the whole document is typed, because that would rule out streaming a large document. The text now says:

> A value's type is fixed once it has been read and every union around it has chosen. Code for it may run then, as a parser reading events does, or once the whole document is typed, as one building a tree may. Either way the calls and their order are the same. So, as with events (part 1, section 2), a parser may already have run code for a document it then refuses, though it never delivers that document as complete. The root's code runs last, once everything inside it is typed, so code that must act on all of a document or none of it belongs there: with `orders: [!order, ...]`, `order`'s code can build each row and `orders`' code save them together.

The engine's way, after the whole document, is one of the two allowed. If the engine ever runs code as it reads, the point where a value's type is fixed under a union of mappings is when one alternative is left (section 3). There are still no suite tests for bindings. Your `calls:` key would let a test check the calls and their order for an accepted document. Since a refused document's calls can now differ between parsers, a test could only check that it is refused.
