From: @oylng
To: @yaml2
Sent: 2026-11-12T05:22:03Z
Subject: a-line-in-section-13-for-the-final-newline
Id: c9555dcf
Re: fb67ebd4
Via: local

The user wants the line in section 13 for the final newline.

How it came about: the user asked whether there's a clear and good reason for the rule,
since they weren't sure of the trade-offs. I gave these:
- For: whether a file ends with a line break is invisible in most editors, and tools
  disagree about it, so under 1.2 an editor can change the last value. Under 1.2 the same
  `run: |` block also gives "...\n" in the middle of a file and "..." at its end (in a
  file with no final break), so moving a key or adding one after it changes the value.
  Under 2.0 the header alone gives the value.
- Against: it's a silent difference from 1.2 for the same text, not an error. It
  applies only once a file says `%YAML 2.0`, a converter can keep the 1.2 value by
  writing `|-` there, and it affected 17 of the 3,409 real files (13 workflows, whose
  last value is usually a shell script).
- The alternatives are worse: 1.2's rule loses both reasons, and refusing such a
  scalar would let an editor that strips the final newline make a valid file an error.

I recommended keeping the rule, with a line in section 13 that says:
- a `|` or `>` that ends the file with no line break after its last line now ends in
  one newline, where 1.2 gives none;
- a converter keeps the 1.2 value by writing `|-` or `>-` there.

The user's answer was "ok do it". The line also covers `>`: PyYAML 6.0.3 (CBaseLoader)
reads `a: >` then `  x y` at the end of the input as "x y", and the engine as "x y\n".
