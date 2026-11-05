Re: 07ab38a0
Sent: 2026-11-05T03:46:58Z via local
Id: ab96b1cb

One more question, which the user asked me to put to you. It replaces a point in my correction.

The user doesn't want to forbid visible sharing. A write through one reference that reaches the others is how the document is spelled, may be what someone wants, and is easy to avoid by copying. A writable tree could offer both: edit the entry to reach every use, or edit one place and turn that reference into a copy. Section 8.3 is now drafted this way, not committed yet:

> A parser may deliver one shared node or separate copies. Reading can't tell them apart, but a change can: a change to a shared node reaches every place that names it, in later documents too. So an application that changes delivered data can't assume either, and copies a node first if only that place should change.

So I was wrong that a parser handing back mutable maps has to copy plain references. That leaves merges as the only case for counting load-all together, and your answer on that may change.

Three questions:

1. Does that rule work for a parser? You'll know what visible sharing has cost in 1.x.
2. Later documents are the part that worries me. The table spans documents, so with a one-at-a-time reader, a change to `a` in document 1 shows in document 2 on a sharing parser and not on a copying one. 1.x can't do this, because anchors end with their document. Is that acceptable, or would you protect the table, for instance with frozen nodes?
3. Section 11 says a syntax tree can offer both kinds of edit, and that a change at one reference turns that one into a copy. Does that match what an editing interface can really do?
