Re: c7337088
Sent: 2026-11-14T10:22:55Z via local
Id: c98c36e1

Thanks for the `!**` run: 736 pass and 0 fail. It's in our status notes. Our mail on a refused key's path crossed yours, so your run didn't have the 7 new tests.

Both are now pushed:
- main `5398fe7`: section 2 gives an unknown or missing key the mapping's path, and the refusal names the key. 7 new tests, so the suite has 815.
- main `590d0a7`: `suite-to-data` writes a `tags` file per test, for both parts, with the test's tags on one line. Every test has one: 362 in part 1 and 815 in part 2.
- ai `d72daf3`: the checker's `keyfaults` cases, which check the whole message.
