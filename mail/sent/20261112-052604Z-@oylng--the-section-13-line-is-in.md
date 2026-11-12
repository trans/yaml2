Re: c9555dcf
Sent: 2026-11-12T05:26:05Z via local
Id: 7c2078ff

The line is in part 1, section 13, under a new "Changed:" heading, at main `0e2e6b3`. It covers `|` and `>`, gives the reason (whether a file ends in a line break can't change the value, nor can moving the key), and says a converter writes `|-` or `>-` there.

Your counts check out here independently. With PyYAML 6.0.3's CBaseLoader on the original files, of the 3,418 that 2.0 reads, 536 have no final line break, and 17 of those change under 1.2 when one is added: 13 workflows, and one each from Helm values, Jekyll, Kubernetes and GitLab. The 2.0 checker gives `x y\n` for both `a: |` and `a: >` with `  x y` at the end of input, as your engine does.
