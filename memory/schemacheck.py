"""Test spec/yaml-schema.md: a throwaway checker written from its text. Not a reference.

    python3 -I schemacheck.py SPEC

Reads every example with the grammar in draftcheck.py, types each document whose local name
is in the table, and compares the result with the example's JSON. Then runs edge cases.
"""
import base64, binascii, datetime, json, os, re, sys
here = os.path.dirname(os.path.abspath(__file__))
src = open(here + '/draftcheck.py', encoding='utf-8').read().split("\nspec = open(sys.argv[1]")[0]
g = {'__name__': 'dc'}; exec(compile(src, 'dc', 'exec'), g)
P, No, read = g['P'], g['No'], g['read']
sys.setrecursionlimit(20000)
class Quoted(str):
    """A scalar not written plain: quoted, or a block scalar."""
for f in ('double', 'single', 'block'):
    def wrap(orig):
        return lambda s, *a: Quoted(orig(s, *a))
    setattr(P, f, wrap(getattr(P, f)))
deliver = P.deliver
def snapshot(s, name, v):
    s.__dict__.setdefault('snaps', []).append(dict(s.table)); deliver(s, name, v)
P.deliver = snapshot

class SchemaError(Exception): pass
class Bad(Exception):
    def __init__(s, path, msg): super().__init__(f'{path or "/"}: {msg}')

STD = {'str', 'int', 'float', 'bool', 'null', 'any', 'date', 'datetime', 'binary'}
INT = r'-?(0|[1-9][0-9]*)'
DATE = r'[0-9]{4}-[0-9]{2}-[0-9]{2}'
DATETIME = DATE + r'[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?([Zz]|[-+][0-9]{2}:[0-9]{2})'

def split(text, sep):
    parts, depth, i, b = [], 0, 0, 0
    while i < len(text):
        if text.startswith('(/', i):
            e = text.find('/)', i + 2)
            if e < 0: raise SchemaError(f'unclosed pattern: {text}')
            i = e + 2; continue
        c = text[i]
        depth += c in '[('; depth -= c in '])'
        if depth == 0 and text.startswith(sep, i):
            parts.append(text[b:i]); i += len(sep); b = i; continue
        i += 1
    return parts + [text[b:]]
def pattern(p, whole):
    cls = False; i = 0
    while i < len(p):
        c = p[i]
        if c == '\\':
            if p[i + 1:i + 2] in tuple('dDwWsSbBAZ123456789'): raise SchemaError(f'not I-Regexp: {whole}')
            i += 2; continue
        if c == '[': cls = True
        elif c == ']': cls = False
        elif not cls and c in '^$': raise SchemaError(f'{c} outside a class: {whole}')
        elif not cls and p.startswith('(?', i): raise SchemaError(f'not I-Regexp: {whole}')
        i += 1
    return ('re', re.compile(p))
def limit(text, name, whole):
    if name not in ('str', 'int', 'float'): raise SchemaError(f'{whole}: only str, int and float take a limit')
    if len(text) > 1 and text[0] == '/' and text[-1] == '/':
        if name != 'str': raise SchemaError(f'{whole}: only str takes a pattern')
        return pattern(text[1:-1], whole)
    m = re.fullmatch(r'(-?[0-9]+(?:\.[0-9]+)?)?\.\.(-?[0-9]+(?:\.[0-9]+)?)?', text)
    if not m or not (m[1] or m[2]): raise SchemaError(f'bad limit: {whole}')
    lo, hi = (None if x is None else float(x) for x in m.groups())
    if lo is not None and hi is not None and lo > hi: raise SchemaError(f'bad limit: {whole}')
    return ('range', lo, hi)
def atom(p):
    if p == "''": return ('lit', '')
    if p.startswith('!'):
        m = re.fullmatch(r'!([^\s()\[\],|/]+)(?:\((.*)\))?', p, re.S)
        if not m: raise SchemaError(f'bad type: {p}')
        return ('name', m[1], None if m[2] is None else m[2], p)
    if p.startswith('['):
        if not p.endswith(']'): raise SchemaError(f'bad sequence: {p}')
        items = [x.strip() for x in split(p[1:-1], ',')]; rest = None
        if items[-1] == '...':
            items.pop()
            if not items: raise SchemaError('`...` repeats the item before it')
            rest = parse(items.pop())
        return ('seq', [parse(i) for i in items], rest)
    if p.startswith('{'): raise SchemaError(f'a mapping in a union must be named: {p}')
    return ('lit', p)
def parse(text):
    alts = [atom(p.strip()) for p in split(text, ' | ')]
    return alts[0] if len(alts) == 1 else ('alt', alts)
def to_type(v):
    if isinstance(v, dict):
        fields, rows = {}, []
        for k, x in v.items():
            if isinstance(k, Quoted): fields[str(k)] = (to_type(x), False)
            elif k.startswith('!'): rows.append((parse(k), to_type(x)))
            elif k.endswith('?'): fields[str(k[:-1])] = (to_type(x), True)
            else: fields[str(k)] = (to_type(x), False)
        return ('map', fields, rows)
    if isinstance(v, list):
        items, rest = list(v), None
        if items and not isinstance(items[-1], Quoted) and items[-1] == '...':
            items.pop()
            if not items: raise SchemaError('`...` repeats the item before it')
            rest = to_type(items.pop())
        return ('seq', [to_type(i) for i in items], rest)
    if isinstance(v, Quoted): return ('lit', str(v))
    return parse(v) if v else ('lit', '')
def strip(v):
    if isinstance(v, dict): return {str(k): strip(x) for k, x in v.items()}
    if isinstance(v, list): return [strip(x) for x in v]
    return str(v)

class Schema:
    def __init__(s, table, root):
        s.table, s.defs, s.memo, s.seen = table, {}, {}, set()
        if root not in table: raise SchemaError(f'no entry {root}')
        s.root = s.get(root); s.walk(s.root)
    def get(s, name):
        if name not in s.defs: s.defs[name] = to_type(s.table[name])
        return s.defs[name]
    def flat(s, t, seen=()):
        if t[0] == 'alt': return [a for x in t[1] for a in s.flat(x, seen)]
        if t[0] != 'name': return [t]
        if t[1] in s.table:
            if t[2] is not None: raise SchemaError(f'{t[3]}: a named type takes no limit')
            if t[1] in seen: raise SchemaError(f'{t[1]} only names itself')
            return s.flat(s.get(t[1]), seen + (t[1],))
        if t[1] not in STD: raise SchemaError(f'unknown type !{t[1]}')
        return [t]
    def alts(s, t):
        m = s.memo.get(id(t))
        if m is None:
            a = []
            for x in s.flat(t):
                if x[0] == 'name' and x[2] is not None and not isinstance(x[2], tuple):
                    x = ('name', x[1], limit(x[2], x[1], x[3]), x[3])
                a.append(x)
            m = s.memo[id(t)] = (t, a)
        return m[1]
    def walk(s, t):
        if id(t) in s.seen: return
        s.seen.add(id(t)); a = s.alts(t)
        if sum(1 for x in a if x[0] == 'seq') > 1: raise SchemaError('more than one sequence alternative')
        for x in a:
            if x[0] == 'seq':
                for y in x[1] + ([x[2]] if x[2] else []): s.walk(y)
            elif x[0] == 'map':
                for ft, _ in x[1].values(): s.walk(ft)
                for kt, vt in x[2]: s.walk(kt); s.walk(vt)
    def check(s, v): return s.conv(s.root, v, '')
    def conv(s, t, v, path):
        a = s.alts(t)
        if len(a) == 1: return s.one(a[0], v, path)
        anys = [x for x in a if x[0] == 'name' and x[1] == 'any']
        if isinstance(v, dict):
            m = [x for x in a if x[0] == 'map']; fit = [x for x in m if s.fits(x, v)]
            if len(fit) == 1: return s.map(fit[0], v, path)
            if anys and not fit: return strip(v)
            raise Bad(path, f'{len(fit)} of {len(m)} mapping alternatives fit')
        if isinstance(v, list):
            q = [x for x in a if x[0] == 'seq']
            if q: return s.one(q[0], v, path)
            if anys: return strip(v)
            raise Bad(path, 'a sequence is not allowed here')
        for x in a:
            if x[0] not in ('lit', 'name'): continue
            try: return s.one(x, v, path)
            except Bad: pass
        raise Bad(path, f'{str(v)[:40]!r} is not allowed here')
    def fits(s, m, v):
        for k, (ft, opt) in m[1].items():
            if k not in v:
                if not opt: return False
                continue
            a = s.alts(ft)
            if all(x[0] == 'lit' for x in a) and v[k] not in [x[1] for x in a]: return False
        return True
    def one(s, x, v, path):
        if x[0] == 'lit':
            if isinstance(v, str) and v == x[1]: return str(v)
            raise Bad(path, f'expected {x[1]!r}')
        if x[0] == 'name': return s.scalar(x[1], x[2], v, path)
        if x[0] == 'map': return s.map(x, v, path)
        if not isinstance(v, list): raise Bad(path, 'expected a sequence')
        if len(v) < len(x[1]) or (x[2] is None and len(v) != len(x[1])): raise Bad(path, f'wrong length: {len(v)}')
        return [s.conv(x[1][i] if i < len(x[1]) else x[2], y, f'{path}/{i}') for i, y in enumerate(v)]
    def map(s, x, v, path):
        if not isinstance(v, dict): raise Bad(path, 'expected a mapping')
        for k, (_, opt) in x[1].items():
            if k not in v and not opt: raise Bad(path, f'missing {k}')
        out = {}
        for k, y in v.items():
            if k in x[1]:
                ft, opt = x[1][k]
                if opt and y == '' and not isinstance(y, Quoted): out[str(k)] = None
                else: out[str(k)] = s.conv(ft, y, f'{path}/{k}')
                continue
            for kt, vt in x[2]:
                try: s.conv(kt, str(k), path)
                except Bad: continue
                out[str(k)] = s.conv(vt, y, f'{path}/{k}'); break
            else: raise Bad(path, f'unknown key {k}')
        return out
    def scalar(s, name, lim, v, path):
        if name == 'any': return strip(v)
        if not isinstance(v, str): raise Bad(path, f'expected {name}')
        if name in ('int', 'float', 'bool', 'null') and isinstance(v, Quoted): raise Bad(path, f'not plain, so not {name}')
        t = str(v); out = None
        try:
            if name == 'str': out = t
            elif name == 'bool' and t in ('true', 'false'): out = t == 'true'
            elif name == 'null' and t == 'null': out = None
            elif name == 'int' and re.fullmatch(INT, t): out = int(t)
            elif name == 'float' and re.fullmatch(INT + r'(\.[0-9]+)?([eE][-+]?[0-9]+)?', t): out = float(t)
            elif name == 'date' and re.fullmatch(DATE, t): datetime.date.fromisoformat(t); out = t
            elif name == 'datetime' and re.fullmatch(DATETIME, t): datetime.datetime.fromisoformat(t.upper().replace('Z', '+00:00')); out = t
            elif name == 'binary': base64.b64decode(t.encode('ascii'), validate=True); out = t
            else: raise ValueError
        except (ValueError, binascii.Error, UnicodeEncodeError): raise Bad(path, f'expected {name}, got {t[:40]!r}')
        if lim and lim[0] == 're':
            if not lim[1].fullmatch(t): raise Bad(path, f'{t[:40]!r} does not match')
        elif lim:
            n = len(t) if name == 'str' else out
            if (lim[1] is not None and n < lim[1]) or (lim[2] is not None and n > lim[2]): raise Bad(path, f'{t[:40]!r} is out of range')
        return out

def typed(stream):
    """Type each document with a local name in the table. Others stay strings."""
    r = read(stream); out = []
    for (name, v), table in zip(r.docs, getattr(r, 'snaps', [])):
        if name and '/' not in name and name in table: out.append(Schema(table, name).check(v))
        else: out.append(strip(v))
    if not r.docs:
        for k in r.table: Schema(r.table, k)
    return out
REFUSED = (No, Bad, SchemaError)
def same(a, b):
    if type(a) is not type(b): return False
    if isinstance(a, dict): return list(a) == list(b) and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list): return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b or (a != a and b != b)

if __name__ == '__main__':
    spec = open(sys.argv[1], encoding='utf-8').read()
    blocks = list(re.finditer(r'```(yaml refused|yaml|json)\n(.*?)```', spec, re.S))
    ok = bad = 0; i = 0
    while i < len(blocks):
        kind, body = blocks[i][1], blocks[i][2]
        if kind == 'yaml refused':
            try: typed(body); bad += 1; print('NOT REFUSED', repr(body))
            except REFUSED: ok += 1
            i += 1; continue
        if kind == 'json': i += 1; continue
        want = None
        if i + 1 < len(blocks) and blocks[i + 1][1] == 'json':
            d = json.JSONDecoder(); t = blocks[i + 1][2].strip(); want = []; k = 0
            while k < len(t):
                v, e = d.raw_decode(t, k); want.append(v); k = e
                while k < len(t) and t[k].isspace(): k += 1
        try:
            got = typed(body)
            if want is None or (len(got) == len(want) and all(same(a, b) for a, b in zip(got, want))): ok += 1
            else: bad += 1; print('DIFFERS', repr(body), got, want)
        except REFUSED as e: bad += 1; print('REFUSED', repr(body), e)
        i += 1
    print(f'spec examples: {ok} pass, {bad} fail')
    H = '--- &\nn: !int\nb: !bool\ns: !str\nd: !date\nt: !datetime\nx: !binary\nf: !float\nz: !null\nr: !int(0..10)\nl: !str(2..3)\np: !str(/[a-z]+/)\no:\n  a?: !str\n  b?: !int\n'
    good = [('n', '3', 3), ('n', '-0', 0), ('f', '3', 3.0), ('f', '1.5e2', 150.0), ('b', 'true', True), ('z', 'null', None), ('s', '3', '3'), ('s', '"3"', '3'), ('d', '2001-02-03', '2001-02-03'), ('d', '"2001-02-03"', '2001-02-03'), ('t', '2001-02-03T04:05:06Z', '2001-02-03T04:05:06Z'), ('x', 'aGk=', 'aGk='), ('r', '0', 0), ('r', '10', 10), ('l', 'ab', 'ab'), ('l', 'abc', 'abc'), ('p', 'abc', 'abc'), ('o', '{}', {}), ('o', 'a:', {'a': None}), ('o', 'a: ""', {'a': ''}), ('o', 'b:', {'b': None})]
    no = [('n', '"3"'), ('n', "'3'"), ('n', '0755'), ('n', '+1'), ('n', '1.0'), ('n', '|\n  3'), ('f', '"3"'), ('f', '1.'), ('f', '.5'), ('b', '"true"'), ('b', 'yes'), ('b', 'True'), ('z', '"null"'), ('z', ''), ('d', '2001-13-01'), ('d', '01/02/2001'), ('t', '2001-02-03'), ('x', 'a b'), ('r', '11'), ('r', '-1'), ('l', 'a'), ('l', 'abcd'), ('p', 'ABC'), ('p', 'abc1'), ('o', 'c: 1'), ('o', 'b: ""'), ('n', '[1]'), ('s', '{a: 1}')]
    f = 0
    for k, v, w in good:
        try: got = typed(H + f'--- !{k}\n{v}\n')[0]; f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', k, v, got)
        except REFUSED as e: f += 1; print('REFUSED', k, v, e)
    for k, v in no:
        try: typed(H + f'--- !{k}\n{v}\n'); f += 1; print('NOT REFUSED', k, repr(v))
        except REFUSED: pass
    schemas = ['a: !nope', 'a: !str(1,2)', 'a: !bool(0..1)', 'a: !int(/x/)', 'a: !int(5..1)', 'a: !a', 'a: !b\nb: !a', 'a: !str(/^x/)', 'a: !str(/x$/)', 'a: !str(/\\d+/)', 'a: !str(/(?=x)/)', 'a: [!a, !b] | [!c]', 'a: !x(1..)\nx: !str', 'a: !str | {b: c}', 'a: [...]', 'a: !a/b', 'a: !str(/x']
    for t in schemas:
        try: typed('--- &\n' + t + '\n'); f += 1; print('SCHEMA NOT REFUSED', t)
        except REFUSED: pass
    print(f'edge cases: {len(good) + len(no) + len(schemas)} run, {f} fail')
    sys.exit(1 if bad or f else 0)
