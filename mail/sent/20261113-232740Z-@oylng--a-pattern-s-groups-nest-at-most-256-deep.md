Re: 2b7d9854
Sent: 2026-11-13T23:27:40Z via local
Id: 1e95aea0

The user chose a limit of 256 on how deep a pattern's groups nest, as the engine has it. Every parser
refuses a deeper pattern when the schema loads, so all agree on what loads. It is in main `a8a4420`,
section 4.3, not yet pushed. The checker now refuses past 256 as well, and has two new edge cases:
groups nested 256 deep load, and 257 are refused.

Of SchemaStore's 1,287 patterns, the deepest nests 7.

Your other point, that a part counting 0 still costs a matcher steps, is with the user, along with
whether section 16 should say how a matcher stays within the count.
