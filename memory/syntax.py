#!/usr/bin/env python3
"""How much real YAML uses each piece of syntax, as a basis for cuts.

    python3 -I syntax.py [--snippets FEATURE] NAME=ROOT...

Prints, per sample, the share of parsed files that use each feature, and uses.
Reads each file with libyaml's events, and goes back to the text through the marks
for what events don't show. Files libyaml can't parse are counted and skipped.
"""
import collections
import hashlib
import os
import re
import sys

import yaml

LOADER = yaml.CSafeLoader
SKIP = {'node_modules', '.git', 'vendor', 'lib', 'target', 'dist', 'build', '.venv',
        'venv', '__pycache__', 'yaml-test-suite', 'corpus', 'fuzz', '.ai', '.cache',
        'site-packages', '.shards', '.bundle'}
ESC = re.compile(r'\\(.)', re.S)
BLOCK = re.compile(r'(?:[&!]\S*\s+)*([|>])([-+0-9]*)')
PLAIN_ESC = {'n': 'common', 't': 'common', '"': 'common', '\\': 'common', 'r': 'common',
             '/': 'rare', '0': 'rare', 'a': 'rare', 'b': 'rare', 'e': 'rare', 'f': 'rare',
             'v': 'rare', 'N': 'rare', '_': 'rare', 'L': 'rare', 'P': 'rare', ' ': 'rare',
             '\n': 'continuation', 'x': 'hex', 'u': 'hex', 'U': 'hex'}


def scan(raw, note):
    """Call note(feature, snippet) for each use in one file's bytes."""
    if raw[:3] == b'\xef\xbb\xbf':
        note('BOM')
        raw = raw[3:]
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        note('UTF-16')
        return
    text = raw.decode('utf-8')
    if '\r\n' in text:
        note('CRLF line ends')
    spans, stack, line_docs = [], [], 0
    events = list(yaml.parse(text, Loader=LOADER))
    pending_root = False
    for i, e in enumerate(events):
        top = stack[-1] if stack else None
        if isinstance(e, yaml.DocumentStartEvent):
            line_docs += 1
            pending_root = True
            start = e.start_mark
            if e.explicit:
                note('--- marker')
            if e.version:
                note('%YAML directive')
            if e.tags:
                note('%TAG directive')
        elif isinstance(e, yaml.DocumentEndEvent):
            if e.explicit:
                note('... marker')
        elif isinstance(e, yaml.ScalarEvent):
            s, f = e.start_mark, e.end_mark
            src = text[s.index:f.index]
            spans.append((s.index, f.index))
            if pending_root:
                note('scalar as a whole document', src[:50])
            plain = e.implicit[0]
            iskey = top and top['kind'] == 'map' and top['want'] == 'key'
            m = BLOCK.match(src) if not plain and e.style in ('|', '>') else None
            if m:
                note('block scalar, any')
                note('block ' + m.group(1), src[:40])
                head = m.group(2)
                if '+' in head:
                    note('block keep chomp, |+ >+', src[:40])
                if '-' in head:
                    note('block strip chomp, |- >-')
                if re.search(r'\d', head):
                    note('block indent indicator, |2', src[:40])
                if not head:
                    note('block default chomp, | >')
                if m.group(1) == '>' and re.search(r'\n[ \t]', e.value.rstrip('\n')):
                    note('folded with more-indented lines', src[:50])
            elif plain:
                if e.value == '' and top:
                    note('empty value in a sequence' if top['kind'] == 'seq' else 'empty value, key:')
                if s.line != f.line:
                    note('multi-line plain scalar', src[:60])
            else:
                note('quoted key' if iskey else 'quoted value')
                note(e.style + ' quoted, any')
                if e.style == "'" and "''" in src[1:-1]:
                    note("'' inside single quotes")
                if s.line != f.line:
                    note('multi-line quoted scalar', src[:60])
                if e.style == '"':
                    for c in ESC.findall(src):
                        note('escape: ' + PLAIN_ESC.get(c, 'other'), '\\' + c)
            if iskey and s.line != f.line:
                note('multi-line key', src[:50])
            pending_root = False
            if top and top['kind'] == 'map':
                top['want'] = 'value' if top['want'] == 'key' else 'key'
        elif isinstance(e, yaml.CollectionStartEvent):
            ismap = isinstance(e, yaml.MappingStartEvent)
            s = e.start_mark
            prefix = text[max(0, s.index - s.column):s.index]
            if e.flow_style:
                note('flow, any')
                note('flow { }' if ismap else 'flow [ ]')
                if ismap and text[s.index] != '{':
                    note('one-pair mapping in [ ]', text[s.index:s.index + 40])
                if top and top['flow']:
                    note('flow inside flow')
            elif top and not top['flow']:
                if not ismap and top['kind'] == 'seq' and prefix.rstrip().endswith('-'):
                    note('compact - - nested sequence', text[s.index - 2:s.index + 20])
                if ismap and top['kind'] == 'seq' and prefix.rstrip().endswith('-'):
                    note('compact - key: mapping')
                if not ismap and top['kind'] == 'map' and s.column == top['col']:
                    note('zero-indented sequence')
            if pending_root and not e.flow_style:
                pass
            pending_root = False
            if top and top['kind'] == 'map':
                top['want'] = 'value' if top['want'] == 'key' else 'key'
            stack.append({'kind': 'map' if ismap else 'seq', 'want': 'key', 'flow': bool(e.flow_style),
                          'col': s.column, 'line': s.line, 'start': s.index})
        elif isinstance(e, yaml.CollectionEndEvent):
            t = stack.pop()
            if t['flow']:
                f = e.end_mark
                if t['line'] != f.line:
                    note('multi-line flow')
                if re.search(r',\s*$', text[t['start']:f.index - 1]):
                    note('trailing comma in flow')
        elif isinstance(e, yaml.AliasEvent):
            if top and top['kind'] == 'map':
                top['want'] = 'value' if top['want'] == 'key' else 'key'
    if line_docs > 1:
        note('more than one document')
    # tabs outside any scalar and before any comment
    spans.sort()
    for m in re.finditer('\t', text):
        p = m.start()
        lo, hi = 0, len(spans)
        while lo < hi:
            mid = (lo + hi) // 2
            if spans[mid][1] <= p:
                lo = mid + 1
            else:
                hi = mid
        if lo < len(spans) and spans[lo][0] <= p:
            continue
        begin = text.rfind('\n', 0, p) + 1
        if '#' in text[begin:p]:
            continue
        note('tab as whitespace', repr(text[begin:p + 12]))
        break


def walk(root, snippets, want):
    seen, files, uses, parsed, failed = set(), collections.Counter(), collections.Counter(), 0, 0
    for d, dirs, names in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for f in names:
            if not f.endswith(('.yml', '.yaml')):
                continue
            path = os.path.join(d, f)
            try:
                raw = open(path, 'rb').read(5 << 20)
            except OSError:
                continue
            h = hashlib.sha1(raw).digest()
            if h in seen:
                continue
            seen.add(h)
            if b'/url:' in raw or b'[ref=e' in raw:     # browser snapshots, not YAML by hand
                continue
            found = collections.Counter()
            def note(k, snippet=None):
                found[k] += 1
                if k == want and snippet is not None:
                    snippets.append(snippet)
            try:
                scan(raw, note)
            except Exception:
                failed += 1
                continue
            parsed += 1
            uses.update(found)
            files.update(found.keys())
    return parsed, failed, files, uses


if __name__ == '__main__':
    args = sys.argv[1:]
    want = None
    if args[0] == '--snippets':
        want, args = args[1], args[2:]
    results, snippets = {}, []
    for arg in args:
        name, root = arg.split('=', 1)
        results[name] = walk(root, snippets, want)
    if want:
        for s in snippets[:40]:
            print(repr(s))
        sys.exit()
    names = list(results)
    print(f'{"":36}' + ''.join(f'{n[:9]:>10}' for n in names) + f'{"uses":>10}')
    print(f'{"files parsed":36}' + ''.join(f'{results[n][0]:>10}' for n in names))
    print(f'{"files failed":36}' + ''.join(f'{results[n][1]:>10}' for n in names))
    keys = sorted({k for r in results.values() for k in r[2]})
    for k in keys:
        row = ''.join(f'{100 * results[n][2][k] / max(1, results[n][0]):>9.1f}%' for n in names)
        print(f'{k:36}{row}{sum(results[n][3][k] for n in names):>10}')
