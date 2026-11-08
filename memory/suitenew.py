"""Add a test to part 1's suite: the stream on standard input, the answers from draftcheck.py.

    python3 -I suitenew.py SUITE 'NAME' SECTION 'TAGS' [fail] [limit=N] [keep] [together] < stream

Writes SUITE/src/ID.yaml in the suite's format (suite/README.md) and prints it. The tree, the JSON
and the rest come from the checker, so read them before keeping the test: a test that only repeats
the checker tests nothing. Refuses if the checker doesn't give the outcome asked for. The ID is made
from the test, as the first 350 were made on 2026-11-08.
"""
import hashlib, json, os, re, sys
here = os.path.dirname(os.path.abspath(__file__))
g = {}
exec(open(here + '/draftcheck.py', encoding='utf-8').read().split("\nspec = open(sys.argv[1]")[0], g)
P, No = g['P'], g['No']
DEFAULT = 64 * 2 ** 20
MARKS = '␣»—←⇔↵∎'
ESCAPED = re.compile('[\x00-\x1f\x7f-\x9f ­ ᠎ -‏ -  -⁯　﻿￹-￻￾￿' + MARKS + ']')
NAMED = {'\\': '\\\\', '\0': '\\0', '\b': '\\b', '\t': '\\t', '\n': '\\n', '\r': '\\r'}

def esc(s): return ''.join(NAMED.get(c) or (f'\\u{ord(c):04X}' if ESCAPED.match(c) else c) for c in s)
def visible(text):
    """The lines of a | block that unescapes to text, or None if it needs double quotes."""
    if not text or any(ESCAPED.match(c) and c not in '\t\n\r' for c in text): return None
    final = text.endswith('\n')
    out = []
    for l in (text[:-1] if final else text).split('\n'):
        s = ''; end = len(l.rstrip(' \t\r'))
        for i, c in enumerate(l):
            if c == '\t': s += '—' * (3 - len(s) % 4) + '»'
            elif c == '\r': s += '←'
            elif c == ' ' and i >= end: s += '␣'
            else: s += c
        out.append(s)
    k = len(out) - 1
    while k >= 0 and out[k] == '': out[k] = '↵'; k -= 1
    if not final: out[-1] += '∎'
    return out
def dq(text):
    return '"' + ''.join({'\\': '\\\\', '"': '\\"', '\n': '\\n', '\t': '\\t', '\r': '\\r'}.get(c) or (f'\\u{ord(c):04X}' if ESCAPED.match(c) else c) for c in text) + '"'
def field(key, text):
    if text == '': return [f"  {key}: ''"]
    v = visible(text)
    if v is None: return [f'  {key}: {dq(text)}']
    first = next((l for l in v if l not in ('', '↵')), '')
    return [f'  {key}: |' + ('2' if first.startswith(' ') else '')] + [('    ' + l) if l else '' for l in v]
def events(docs):
    out = ['+STR']
    def node(v, d):
        if isinstance(v, str): out.append(' ' * d + '=VAL :' + esc(v))
        elif isinstance(v, list):
            out.append(' ' * d + '+SEQ'); [node(x, d + 1) for x in v]; out.append(' ' * d + '-SEQ')
        else:
            out.append(' ' * d + '+MAP')
            for k, x in v.items(): node(k, d + 1); node(x, d + 1)
            out.append(' ' * d + '-MAP')
    for name, v in docs:
        out.append(' +DOC' + (' !' + esc(name) if name else '')); node(v, 2); out.append(' -DOC')
    return '\n'.join(out + ['-STR']) + '\n'
def jline(v):
    return ''.join(f'\\u{ord(c):04x}' if ESCAPED.match(c) else c for c in json.dumps(v, ensure_ascii=False))
def quoted(s):
    return s if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ,.()+/=-]*[A-Za-z0-9.)]", s) else "'" + s.replace("'", "''") + "'"
def ident(key, taken):
    alpha = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; salt = 0
    while True:
        h = int.from_bytes(hashlib.sha256((key + '\0' + str(salt)).encode('utf-8', 'surrogatepass')).digest(), 'big')
        for _ in range(40):
            i = ''.join(alpha[(h >> (5 * k)) & 31] for k in range(4)); h >>= 20
            if re.search('[A-Z]', i) and re.search('[0-9]', i) and i not in taken: return i
        salt += 1

def main(suite, name, section, tags, *flags):
    text = sys.stdin.buffer.read().decode('utf-8')
    o = {}
    for f in flags:
        if f.startswith('limit='): o['limit'] = int(f[6:])
        elif f in ('fail', 'keep', 'together'): o[f] = True
        else: sys.exit(f'unknown flag {f}')
    try: r = P(text, o.get('limit', DEFAULT), o.get('together', False), o.get('keep', False)).stream().finish()
    except No as e: r = e
    if isinstance(r, No) != bool(o.get('fail')): sys.exit(f'the checker gives {r if isinstance(r, No) else "data"}')
    tags = ' '.join(dict.fromkeys(tags.split() + (['error'] if o.get('fail') else [])))
    lines = ['---', f'- name: {quoted(name)}', f'  from: part 1, section {section}', f'  tags: {tags}']
    if o.get('fail'): lines.append('  fail: true')
    if 'limit' in o: lines.append(f"  limit: {o['limit']}")
    for f in ('keep', 'together'):
        if o.get(f): lines.append(f'  {f}: true')
    lines += field('yaml', text)
    if not o.get('fail') and not o.get('keep'):
        lines += field('tree', events(r.docs))
        lines += field('json', ''.join(jline(d[1]) + '\n' for d in r.docs))
        if r.offset() is not None:
            lines += field('rest', text.encode('utf-8', 'surrogatepass')[r.offset():].decode('utf-8', 'surrogatepass'))
    src = os.path.join(suite, 'src')
    i = ident(text + '\0' + json.dumps(sorted(o.items())), {f[:-5] for f in os.listdir(src)})
    path = os.path.join(src, i + '.yaml')
    with open(path, 'w', encoding='utf-8') as f: f.write('\n'.join(lines) + '\n')
    print(path); print('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv) < 5: sys.exit(__doc__.strip())
    main(*sys.argv[1:])
