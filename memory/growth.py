#!/usr/bin/env python3
"""How far references expand real YAML, and what limit that leaves room for.

    python3 -I growth.py ROOT...
    python3 -I growth.py --check K FILE...    # where cost > K * written refuses
    python3 -I growth.py --total N FILE...    # where written + cost > N refuses

Size: 1 per node, plus the bytes of each scalar. A reference costs the full size of
what it names, with no dedupe, so `<<` over a shared key still counts. `written` is
what the file spells out. `floor(k)` is the smallest F for which `cost <= F + k *
written` holds at every reference, in file order, across a sample.
"""
import hashlib
import os
import statistics
import sys

import yaml

LOADER = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
SKIP = {'node_modules', '.git', 'vendor', 'yaml-test-suite', 'corpus', 'fuzz'}
KS = (1, 2, 5, 10, 20, 50, 100)


def steps(events):
    """Yield (written, cost) after each reference, in file order, then at the end."""
    written = cost = 0
    anchors, stack = {}, [[0, None]]
    for e in events:
        if isinstance(e, yaml.ScalarEvent):
            n = 1 + len(e.value.encode('utf-8', 'replace'))
            written += n
            stack[-1][0] += n
            if e.anchor:
                anchors[e.anchor] = n
        elif isinstance(e, yaml.CollectionStartEvent):
            written += 1
            stack.append([1, e.anchor])
        elif isinstance(e, yaml.CollectionEndEvent):
            n, anchor = stack.pop()
            stack[-1][0] += n
            if anchor:
                anchors[anchor] = n
        elif isinstance(e, yaml.AliasEvent):
            n = anchors.get(e.anchor, 0)
            written += 1 + len(e.anchor)
            cost += n
            stack[-1][0] += n
            yield written, cost
    yield written, cost


def measure(events):
    """Return (written, cost, {k: largest excess over k * written})."""
    written = cost = 0
    excess = {k: 0 for k in KS}
    for written, cost in steps(events):
        for k in KS:
            excess[k] = max(excess[k], cost - k * written)
    return written, cost, excess


def check(path, k):
    """Print the reference at which `cost > k * written` first holds."""
    uses = 0
    for written, cost in steps(yaml.parse(open(path, 'rb').read(), Loader=LOADER)):
        uses += 1
        if cost > k * written:
            print(f'{os.path.basename(path)}: refused at reference {uses}, '
                  f'written {written:,}, cost {cost:,}')
            return
    print(f'{os.path.basename(path)}: accepted, written {written:,}, cost {cost:,}, '
          f'{uses - 1} references')


def scan(root):
    seen, rows = set(), []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in files:
            if not f.endswith(('.yml', '.yaml')):
                continue
            try:
                data = open(os.path.join(d, f), 'rb').read()
                h = hashlib.sha1(data).digest()
                if h in seen:
                    continue
                seen.add(h)
                rows.append((f, *measure(yaml.parse(data, Loader=LOADER))))
            except Exception:
                continue
    return rows


def total(path, limit):
    """Print the reference at which `written + cost > limit` first holds."""
    uses = 0
    for written, cost in steps(yaml.parse(open(path, 'rb').read(), Loader=LOADER)):
        uses += 1
        if written + cost > limit:
            print(f'{os.path.basename(path)}: refused at reference {uses}, '
                  f'written {written:,}, cost {cost:,}')
            return
    print(f'{os.path.basename(path)}: accepted, total {written + cost:,}')


def report(name, rows):
    used = [r for r in rows if r[2]]
    print(f'{name}: {len(rows)} files, {len(used)} with references')
    if not used:
        return
    ratio = sorted((w + c) / w for _, w, c, _ in used)
    pick = lambda q: ratio[min(len(ratio) - 1, int(q * len(ratio)))]
    print(f'  expanded / written: median {statistics.median(ratio):.2f}, '
          f'90% {pick(.9):.2f}, 99% {pick(.99):.2f}, max {ratio[-1]:.2f}')
    print(f'  largest cost {max(r[2] for r in used):,}')
    sizes = sorted(w + c for _, w, c, _ in rows)
    print(f'  total size, all {len(sizes)} files: median {sizes[len(sizes) // 2]:,}, '
          f'99.9% {sizes[int(.999 * len(sizes))]:,}, top {sizes[-3:]}')
    print('  floor needed: ' + ', '.join(
        f'k={k}: {max(r[3][k] for r in used):,}' for k in KS))


if __name__ == '__main__':
    if sys.argv[1] in ('--check', '--total'):
        for path in sys.argv[3:]:
            (check if sys.argv[1] == '--check' else total)(path, int(sys.argv[2]))
        sys.exit()
    everything = []
    for root in sys.argv[1:]:
        rows = scan(root)
        report(os.path.basename(root.rstrip('/')), rows)
        everything += rows
    if len(sys.argv) > 2:
        report('all', everything)
