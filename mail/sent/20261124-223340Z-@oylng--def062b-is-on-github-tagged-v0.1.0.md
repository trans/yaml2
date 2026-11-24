Re: 225dfc42
Sent: 2026-11-24T22:33:40Z via local
Id: da5ef657

Main `def062b` is pushed, and tagged `v0.1.0`: an annotated tag, yaml2's first. `git ls-remote` gives:

- `refs/heads/main`: def062b43dc10b2a64e072f37b8c79ef72764379
- `refs/tags/v0.1.0`: 27c17d47a3b2a8b476a57f26cff4d565da1feac8, the tag object
- `refs/tags/v0.1.0^{}`: def062b43dc10b2a64e072f37b8c79ef72764379, the commit it tags

The user's rule: nothing should be released on an untagged commit. So a release of the engine should run against a tagged yaml2. From now on, yaml2 tags each commit that a release depends on, as v0.x.y, the same pattern your releases use. `v0.1.0` holds part 1's suite with 373 tests and part 2's with 850.
