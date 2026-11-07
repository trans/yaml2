"""Test spec/yaml-schema.md: a throwaway checker written from its text. Not a reference.

    python3 -I schemacheck.py SPEC

Reads every example with the grammar in draftcheck.py, types each document whose local name
is in the table, and compares the result with the example's JSON. Then runs edge cases.
"""
import base64, binascii, datetime, hashlib, json, math, os, re, re._parser, sys
from decimal import Context, Decimal, InvalidOperation, MAX_EMAX, MIN_EMIN
here = os.path.dirname(os.path.abspath(__file__))
src = open(here + '/draftcheck.py', encoding='utf-8').read().split("\nspec = open(sys.argv[1]")[0]
g = {'__name__': 'dc'}; exec(compile(src, 'dc', 'exec'), g)
P, No, read = g['P'], g['No'], g['read']
sys.setrecursionlimit(20000); sys.set_int_max_str_digits(0)
class Quoted(str):
    """A scalar not written plain: quoted, or a block scalar."""
for f in ('double', 'single', 'block'):
    def wrap(orig):
        return lambda s, *a: Quoted(orig(s, *a))
    setattr(P, f, wrap(getattr(P, f)))
deliver = P.deliver
def snapshot(s, name, v):
    s.__dict__.setdefault('snaps', []).append((dict(s.table), s.table)); deliver(s, name, v)
P.deliver = snapshot

class SchemaError(Exception): pass
class Bad(Exception):
    def __init__(s, path, msg): super().__init__(f'{path or "/"}: {msg}')
class Cant(Exception):
    """A number that can't be held. It refuses the document, and isn't a failed match."""
def lost(t, f):
    """Is what is stored more than half a unit of the last written digit from what is written?"""
    d = Decimal(t)
    if d == 0: return False
    if math.isinf(f): return True
    c = Context(prec=len(t) + 1100, Emax=MAX_EMAX, Emin=MIN_EMIN)
    return c.multiply(abs(c.subtract(Decimal(f), d)), Decimal(2)) > c.scaleb(Decimal(1), d.as_tuple().exponent)

STD = {'str', 'int', 'float', 'decimal', 'bool', 'null', 'any', 'date', 'datetime', 'binary'}
FLOAT = r'-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?'
INT = r'-?(0|[1-9][0-9]*)'
READINT = r'[-+]?[0-9]+'
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
    if name not in ('str', 'int', 'float', 'decimal'): raise SchemaError(f'{whole}: only str and numbers take a limit')
    if len(text) > 1 and text[0] == '/' and text[-1] == '/':
        if name not in ('str', 'int'): raise SchemaError(f'{whole}: only str and int take a pattern')
        return pattern(text[1:-1], whole)
    m = re.fullmatch(r'(-?[0-9]+(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?)?\.\.(-?[0-9]+(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?)?', text)
    if not m or not (m[1] or m[2]): raise SchemaError(f'bad limit: {whole}')
    lo, hi = (None if x is None else Decimal(x) for x in m.groups())
    if lo is not None and hi is not None and lo > hi: raise SchemaError(f'bad limit: {whole}')
    return ('range', lo, hi)
def atom(p):
    if not p: raise SchemaError('an empty part')
    if p == "''": return ('lit', '')
    if p == '[]': return ('seq', [], None)
    if p[:1] in ('"', "'"): raise SchemaError(f'a part can only start with a quote as two single quotes: {p}')
    if p.startswith('!'):
        m = re.fullmatch(r'!([^ \t()\[\],|/]+)(?:\((.*)\))?', p, re.S)
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
        fields, rows, deep, other = {}, [], None, None
        for k, x in v.items():
            if isinstance(k, Quoted): fields[str(k)] = (to_type(x), False)
            elif k == '!**': deep = rule(x)
            elif k == '!*': other = to_type(x)
            elif k.startswith('!'): rows.append((parse(k), to_type(x)))
            elif k.endswith('?'): fields[str(k[:-1])] = (to_type(x), True)
            else: fields[str(k)] = (to_type(x), False)
        return ('map', fields, rows, deep, other)
    if isinstance(v, list):
        items, rest = list(v), None
        if items and not isinstance(items[-1], Quoted) and items[-1] == '...':
            items.pop()
            if not items: raise SchemaError('`...` repeats the item before it')
            rest = to_type(items.pop())
        return ('seq', [to_type(i) for i in items], rest)
    if isinstance(v, Quoted): return ('lit', str(v))
    return parse(v) if v else ('lit', '')
def rule(x):
    """What `!**` holds: named keys, type keys, and in `!*` a type for every other scalar."""
    if isinstance(x, dict):
        t = to_type(x)
        if t[3] is not None: raise SchemaError('a `!**` holds no `!**`')
        return (t[1], t[2], t[4])
    return ({}, [], to_type(x))
def strip(v):
    if isinstance(v, dict): return {str(k): strip(x) for k, x in v.items()}
    if isinstance(v, list): return [strip(x) for x in v]
    return str(v)

CEILING = 1024
LIMIT = 64 * 2 ** 20
def size(tree):
    """Positions in a parsed pattern, after nested counts multiply."""
    t = 0
    for op, av in tree:
        n = str(op)
        if n in ('MAX_REPEAT', 'MIN_REPEAT'):
            lo, hi, sub = av
            t += max(lo if str(hi) == 'MAXREPEAT' else hi, 1) * size(sub)
        elif n == 'SUBPATTERN': t += size(av[3])
        elif n == 'BRANCH': t += sum(size(x) for x in av[1])
        elif n != 'AT': t += 1
    return t

class Schema:
    def __init__(s, table, root, accept=False, limit=LIMIT):
        s.table, s.defs, s.memo, s.seen, s.reached, s.accept = table, {}, {}, set(), {root}, accept
        s.places, s.fulls = {}, {}
        if root not in table: raise SchemaError(f'no entry {root}')
        s.root = s.get(root); s.walk(s.root)
        for name in s.reached: s.place(s.get(name))
        n = sum(s.full(t) for t in s.places.values())
        if n > limit: raise SchemaError(f'a schema of full size {n}')
    def place(s, t): s.places[id(t)] = t
    def full(s, t):
        """What a type expands to. Nothing is deduplicated, as in a stream's full size."""
        if t[0] == 'alt': return sum(s.full(x) for x in t[1])
        if t[0] == 'name' and t[1] in s.table:
            if t[1] not in s.fulls: s.fulls[t[1]] = s.full(s.get(t[1]))
            return 1 + s.fulls[t[1]]
        if t[0] == 'name' and t[2] and t[2][:1] == '/': return size(re._parser.parse(t[2][1:-1]))
        if t[0] == 'lit': return 1
        if t[0] == 'map':
            n = 1 + len(t[1]) + len(t[2]) + (t[4] is not None)
            return n + (len(t[3][0]) + len(t[3][1]) + (t[3][2] is not None) if t[3] else 0)
        return 1
    def get(s, name):
        if name not in s.defs: s.defs[name] = to_type(s.table[name])
        return s.defs[name]
    def flat(s, t, seen=(), done=None):
        if done is None: done = set()
        if t[0] == 'alt': return [a for x in t[1] for a in s.flat(x, seen, done)]
        if t[0] != 'name': return [t]
        if t[1] in s.table:
            if t[2] is not None: raise SchemaError(f'{t[3]}: a named type takes no limit')
            if t[1] in seen: raise SchemaError(f'{t[1]} only names itself')
            if t[1] in done: return []
            done.add(t[1]); s.reached.add(t[1])
            return s.flat(s.get(t[1]), seen + (t[1],), done)
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
            s.ceiling(a)
            m = s.memo[id(t)] = (t, a)
        return m[1]
    def ceiling(s, a):
        n = 0
        for x in a:
            if x[0] == 'lit': continue
            if x[0] == 'name' and x[2] and x[2][0] == 're': n += size(re._parser.parse(x[2][1].pattern))
            else: n += 1
        if n > CEILING: raise SchemaError(f'a union of {n} positions')
    def walk(s, t):
        if id(t) in s.seen: return
        s.seen.add(id(t)); s.place(t); a = s.alts(t)
        if sum(1 for x in a if x[0] == 'seq') > 1: raise SchemaError('more than one sequence alternative')
        for x in a:
            if x[0] == 'seq':
                for y in x[1] + ([x[2]] if x[2] else []): s.walk(y)
            elif x[0] == 'map':
                for ft, _ in x[1].values(): s.walk(ft)
                for kt, vt in x[2]: s.walk(kt); s.walk(vt)
                if x[4] is not None: s.walk(x[4])
                s.ceiling([y for kt, _ in x[2] for y in s.alts(kt)])
                if x[3]:
                    for ft, _ in x[3][0].values(): s.walk(ft)
                    for kt, vt in x[3][1]: s.walk(kt); s.walk(vt)
                    s.ceiling([y for kt, _ in x[3][1] for y in s.alts(kt)])
                    if x[3][2]: s.place(x[3][2])
                    if x[3][2] and any(y[0] not in ('lit', 'name') for y in s.alts(x[3][2])): raise SchemaError('a `!**` takes a scalar type, or a mapping of rules')
    def check(s, v): return s.conv(s.root, v, '')
    def under(s, k, y, path, scope):
        """A key the mapping at this place doesn't name, under the nearest `!**`."""
        fields, rows, _ = scope; p = f'{path}/{k}'
        if k in fields:
            ft, opt = fields[k]
            if opt and y == '' and not isinstance(y, Quoted): return None
            return s.conv(ft, y, p, scope)
        for kt, vt in rows:
            try: s.conv(kt, str(k), path)
            except Bad: continue
            return s.conv(vt, y, p, scope)
        return s.anywhere(y, p, scope)
    def anywhere(s, v, path, scope):
        if isinstance(v, dict): return {str(k): s.under(k, y, path, scope) for k, y in v.items()}
        if isinstance(v, list): return [s.anywhere(y, f'{path}/{i}', scope) for i, y in enumerate(v)]
        return s.conv(scope[2], v, path, scope) if scope[2] else strip(v)
    def conv(s, t, v, path, scope=None):
        a = s.alts(t)
        if len(a) == 1: return s.one(a[0], v, path, scope)
        anys = [x for x in a if x[0] == 'name' and x[1] == 'any']
        if isinstance(v, dict):
            m = [x for x in a if x[0] == 'map']; fit = [x for x in m if s.fits(x, v, scope)]
            if len(fit) == 1: return s.map(fit[0], v, path, scope)
            if anys and not fit: return strip(v)
            raise Bad(path, f'{len(fit)} of {len(m)} mapping alternatives fit')
        if isinstance(v, list):
            q = [x for x in a if x[0] == 'seq']
            if q: return s.one(q[0], v, path, scope)
            if anys: return strip(v)
            raise Bad(path, 'a sequence is not allowed here')
        for x in a:
            if x[0] not in ('lit', 'name'): continue
            try: return s.one(x, v, path, scope)
            except Bad: pass
        raise Bad(path, f'{str(v)[:40]!r} is not allowed here')
    def fits(s, m, v, scope=None):
        for k, (ft, opt) in m[1].items():
            if k not in v:
                if not opt: return False
                continue
            a = s.alts(ft)
            if all(x[0] == 'lit' for x in a) and v[k] not in [x[1] for x in a]: return False
        if m[3] or m[4] is not None or scope: return True
        for k in v:
            if k in m[1]: continue
            for kt, _ in m[2]:
                try: s.conv(kt, str(k), '')
                except Bad: continue
                break
            else: return False
        return True
    def one(s, x, v, path, scope=None):
        if x[0] == 'lit':
            if isinstance(v, str) and v == x[1]: return str(v)
            raise Bad(path, f'expected {x[1]!r}')
        if x[0] == 'name': return s.scalar(x[1], x[2], v, path)
        if x[0] == 'map': return s.map(x, v, path, scope)
        if not isinstance(v, list): raise Bad(path, 'expected a sequence')
        if len(v) < len(x[1]) or (x[2] is None and len(v) != len(x[1])): raise Bad(path, f'wrong length: {len(v)}')
        return [s.conv(x[1][i] if i < len(x[1]) else x[2], y, f'{path}/{i}', scope) for i, y in enumerate(v)]
    def map(s, x, v, path, scope=None):
        if x[3]: scope = x[3]
        if not isinstance(v, dict):
            if x[3] and all(o for _, o in x[1].values()): return s.anywhere(v, path, scope)
            raise Bad(path, 'expected a mapping')
        for k, (_, opt) in x[1].items():
            if k not in v and not opt: raise Bad(path, f'missing {k}')
        out = {}
        for k, y in v.items():
            if k in x[1]:
                ft, opt = x[1][k]
                if opt and y == '' and not isinstance(y, Quoted): out[str(k)] = None
                else: out[str(k)] = s.conv(ft, y, f'{path}/{k}', scope)
                continue
            for kt, vt in x[2]:
                try: s.conv(kt, str(k), path)
                except Bad: continue
                out[str(k)] = s.conv(vt, y, f'{path}/{k}', scope); break
            else:
                if x[4] is not None: out[str(k)] = s.conv(x[4], y, f'{path}/{k}', scope)
                elif not scope: raise Bad(path, f'unknown key {k}')
                else: out[str(k)] = s.under(k, y, path, scope)
        return out
    def scalar(s, name, lim, v, path):
        if name == 'any': return strip(v)
        if not isinstance(v, str): raise Bad(path, f'expected {name}')
        if name in ('int', 'float', 'decimal', 'bool', 'null') and isinstance(v, Quoted): raise Bad(path, f'not plain, so not {name}')
        t = str(v); out = None
        try:
            if name == 'str': out = t
            elif name == 'bool' and t in ('true', 'false'): out = t == 'true'
            elif name == 'null' and t == 'null': out = None
            elif name == 'int' and lim and lim[0] == 're':
                if not lim[1].fullmatch(t): raise Bad(path, f'{t[:40]!r} does not match')
                if not re.fullmatch(READINT, t): raise Cant(f'{path or "/"}: {t[:40]!r} matched, and is not an integer')
                out = int(t)
            elif name == 'int' and re.fullmatch(INT, t): out = int(t)
            elif name == 'float' and re.fullmatch(FLOAT, t):
                out = float(t)
                if math.isinf(out): raise Cant(f'{path or "/"}: {t[:40]} is too large to hold')
                if lost(t, out) and not s.accept: raise Cant(f'{path or "/"}: {t[:40]} would lose digits')
            elif name == 'decimal' and re.fullmatch(FLOAT, t): out = Decimal(t)
            elif name == 'date' and re.fullmatch(DATE, t): datetime.date.fromisoformat(t); out = t
            elif name == 'datetime' and re.fullmatch(DATETIME, t): datetime.datetime.fromisoformat(t.upper().replace('Z', '+00:00')); out = t
            elif name == 'binary': t = t.replace('\n', ''); base64.b64decode(t.encode('ascii'), validate=True); out = t
            else: raise ValueError
        except (ValueError, binascii.Error, UnicodeEncodeError): raise Bad(path, f'expected {name}, got {t[:40]!r}')
        if lim and lim[0] == 're':
            if name == 'str' and not lim[1].fullmatch(t): raise Bad(path, f'{t[:40]!r} does not match')
        elif lim:
            n = len(t) if name == 'str' else out
            if (lim[1] is not None and n < lim[1]) or (lim[2] is not None and n > lim[2]): raise Bad(path, f'{t[:40]!r} is out of range')
        return out

PUB = re.compile(r'[^/]+(?:/[^/]+)*/([0-9a-f]{40})\.yes')
def published(name, store, accept, limit=LIMIT):
    """Section 3.1. The store is what an application can get, by hash, from anywhere."""
    h = PUB.fullmatch(name)[1]; b = store.get(h)
    if b is None: raise Cant(f'{name}: the file is not to be had')
    if hashlib.sha256(b).hexdigest()[:40] != h: raise Cant(f'{name}: the file does not hash to its name')
    r = read(b.decode('utf-8'))
    if r.docs or not r.table: raise SchemaError(f'{name}: a published schema is a table and nothing else')
    return Schema(r.table, list(r.table)[-1], accept, limit)
def typed(stream, app=None, accept=False, store=None, limit=LIMIT):
    """Type each stamped document by the file's table, others by the application's schema.
    With neither they stay strings. An application's schema is (schema text, root). A store
    means the application looks published names up."""
    r = read(stream); out = []; reached = {}; live = None
    own = None if app is None else Schema(read(app[0]).table, app[1], accept, limit)
    for (name, v), (table, obj) in zip(r.docs, getattr(r, 'snaps', [])):
        if obj is not live: reached, live = {}, obj
        for k, e in reached.items():
            if table.get(k) is not e: raise SchemaError(f'{k} was replaced after a type reached it')
        if name and '/' not in name and name in table:
            sc = Schema(table, name, accept, limit); out.append(sc.check(v))
            reached.update((k, table[k]) for k in sc.reached)
        elif store is not None and name and PUB.fullmatch(name): out.append(published(name, store, accept, limit).check(v))
        elif own: out.append(own.check(v))
        else: out.append(strip(v))
    if r.docs and r.table is live:
        for k, e in reached.items():
            if r.table.get(k) is not e: raise SchemaError(f'{k} was replaced after a type reached it')
    if not r.docs:
        for k in r.table: Schema(r.table, k)
    return out
REFUSED = (No, Bad, SchemaError, Cant)
def same(a, b):
    if isinstance(a, Decimal): return a == Decimal(repr(b) if isinstance(b, float) else str(b))
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
    schemas = ['"my type": !int\na: !my type', '"my\ttype": !int\na: !my\ttype', 'a: !int | [ ]', 'a: !int | [!int, ]', 'a: !int | [, !int]', 'a: !int | [...]', 'a: !nope', 'a: !str(1,2)', 'a: !bool(0..1)', 'a: !float(/x/)', 'a: !decimal(/x/)', 'a: !bool(/x/)', 'a: !null(/x/)', 'a: !date(/x/)', 'a: !int(/(1{1000}){1000}/)', 'a: !int(/^1/)', 'a: !int(5..1)', 'a: !a', 'a: !b\nb: !a', 'a: !str(/^x/)', 'a: !str(/x$/)', 'a: !str(/\\d+/)', 'a: !str(/(?=x)/)', 'a: [!a, !b] | [!c]', 'a: !x(1..)\nx: !str', 'a: !str | {b: c}', 'a: [...]', 'a: !a/b', 'a: !str(/x', 'a: [!int(0,100), ...]', 'a: {b: !int(0,100)}', 'a: [!str(/[a-z]+/), ...]', 'a: [!str(/(a|b),c/), ...]', 'a: [!str(/[0-9]{2}/), ...]', 'a: {b: !str(/[a-z]+/)}', 'a: {!str(/[a-z]+/): !int}', 'a: !str(/x #y/)', 'a: !str(/x: y/)', 'a: !int | "none"', "a: !int | 'none'", 'a: !b | !int\nb: !a | !str', 'a: !str(/(a{1000}){1000}/)', 'a: !str(/a{1025}/)', 'a: !str(/a{513}/) | !str(/b{512}/)', 'a:\n  !str(/a{513}/): !int\n  !str(/b{512}/): !int']
    for t in schemas:
        try: typed('--- &\n' + t + '\n'); f += 1; print('SCHEMA NOT REFUSED', t)
        except REFUSED: pass
    # A pattern on !int: it replaces the spelling, reads base 10, and a claim it can't read refuses.
    I = '--- &\nq: !int(/[-+][0-9]+/)\nw: !int(/[-+]?[0-9]+/)\nu: !q | !str\nh: !int(/0x[0-9a-f]+/)\nv: !h | !str\nk: !int(/[0-9_]+/)\nar: !int(/[٠-٩]+/)\nfirst: !str | !q\nlit: !q | never\nsome: !int(/[0-9]*/)\no:\n  a: !some\nmk:\n  !q: !str\nby: !int | !str\n'
    ints = [('q', '+5', 5), ('q', '-3', -3), ('q', '+0', 0), ('q', '-0', 0), ('q', '+007', 7), ('w', '5', 5), ('w', '007', 7), ('w', '+5', 5),
                    ('u', '+5', 5), ('u', '+5x', '+5x'), ('u', 'x+5', 'x+5'), ('u', '5', '5'), ('u', '"+5"', '+5'), ('u', "'+5'", '+5'), ('u', 'x', 'x'), ('u', '|\n  +5', '+5\n'), ('v', 'x', 'x'),
                    ('first', '+5', '+5'), ('lit', 'never', 'never'), ('lit', '+5', 5), ('k', '1000', 1000), ('mk', '+5: a\n"-3": b', {'+5': 'a', '-3': 'b'}),
                    ('by', '9' * 5000, int('9' * 5000))]
    for k, v, w in ints:
        try: got = typed(I + f'--- !{k}\n{v}\n')[0]; f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', k, v, got)
        except REFUSED as e: f += 1; print('REFUSED', k, v, e)
    notints = [('q', '5'), ('q', '"+5"'), ('q', "'+5'"), ('q', '|\n  +5'), ('q', '+5x'), ('q', 'x+5'), ('q', '+'), ('q', '[+5]'), ('h', '0x1f'), ('v', '0x1f'),
                 ('k', '1_000'), ('ar', '٣'), ('o', 'a:'), ('lit', '5'), ('mk', '5: a')]
    for k, v in notints:
        try: typed(I + f'--- !{k}\n{v}\n'); f += 1; print('NOT REFUSED', k, repr(v))
        except REFUSED: pass
    # The names are the author's: renaming list and map changes nothing.
    R = '--- &\nsigned: !int(/[-+][0-9]+/)\nfree: !signed | !str | !zig | !zag\nzig: [!free, ...]\nzag:\n  !str: !free\n--- !free\na: +5\nc: [-3, x]\n'
    if not same(typed(R)[0], {'a': 5, 'c': [-3, 'x']}): f += 1; print('DIFFERS renamed')
    # A pattern is a plain scalar first: what still works, and quoting making a literal.
    forms = [('a: !str(/[0-9]{1,3}/)\n--- !a\n"12"\n', '12'), ('a: !str(/x[ ]#y/)\n--- !a\n"x #y"\n', 'x #y'), ('a: !str(/a#b/)\n--- !a\n"a#b"\n', 'a#b'), ('t: !str(/[a-z]+/)\na: [!t, ...]\n--- !a\n- ab\n', ['ab']), ('a: {!str(/x/): !int}\n--- !a\nx: 1\n', {'x': 1}), ('a: ["!str(/[a-z]+/)", ...]\n--- !a\n- "!str(/[a-z]+/)"\n', ['!str(/[a-z]+/)'])]
    for t, w in forms:
        try: got = typed('--- &\n' + t)[0]; f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', repr(t), got)
        except REFUSED as e: f += 1; print('REFUSED', repr(t), e)
    try: typed('--- &\na: ["!str(/[a-z]+/)", ...]\n--- !a\n- ab\n'); f += 1; print('QUOTED PATTERN NOT A LITERAL')
    except REFUSED: pass
    # Who says: the file's stamp, then the application, then strings.
    J = ('--- &\njob:\n  retries: !int\n', 'job')
    says = [('retries: 3\n', {'retries': 3}), ('--- &\njob:\n  retries: !any\n--- !job\nretries: abc\n', {'retries': 'abc'}), ('--- &\nint: !str\njob:\n  retries: !int\n--- !job\nretries: abc\n', {'retries': 'abc'}), ('--- &\njob: data\n---\nretries: 3\n', {'retries': 3}), ('--- &\njob: data\n--- !other\nretries: 3\n', {'retries': 3}), ('--- !a.example/job\nretries: 3\n', {'retries': 3})]
    for t, w in says:
        try: got = typed(t, J)[0]; f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', repr(t), got)
        except REFUSED as e: f += 1; print('REFUSED', repr(t), e)
    for t in ('retries: abc\n', '--- &\njob: data\n---\nretries: abc\n'):
        try: typed(t, J); f += 1; print('NOT REFUSED', repr(t))
        except REFUSED: pass
    # Unions: fit is closed, each name counts once, and !any takes what nothing else fits.
    unions = [('u: !int | []\n--- !u\n[]\n', []), ('u: !int | []\n--- !u\n5\n', 5), ('u: !int | [!int, []]\n--- !u\n[1, []]\n', [1, []]), ('e: []\n--- !e\n[]\n', []), ('"a\xa0b": !int\nu: !a\xa0b\n--- !u\n3\n', 3), ('m:\n  x: !int\nu: !m | !m\n--- !u\nx: 1\n', {'x': 1}), ('m:\n  x: !int\nv: !m | !int\nw: !m | !str\nu: !v | !w\n--- !u\nx: 1\n', {'x': 1}), ('a:\n  x?: !int\nb:\n  y?: !int\nu: !a | !b\n--- !u\nx: 1\n', {'x': 1}), ('m:\n  x: !int\nu: !m | !any\n--- !u\ny: 1\n', {'y': '1'}), ('a: !str(/a{1024}/)\n--- !a\n' + 'a' * 1024 + '\n', 'a' * 1024), ('a: !str(/a{512}/) | !str(/b{512}/)\n--- !a\n' + 'b' * 512 + '\n', 'b' * 512), ('u: !int | one | two\n--- !u\ntwo\n', 'two')]
    for t, w in unions:
        try: got = typed('--- &\n' + t)[0]; f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', repr(t), got)
        except REFUSED as e: f += 1; print('REFUSED', repr(t), e)
    # `!**`: here and below, the closest rule wins, and only the nearest `!*` counts.
    S = 'signed: !int(/[-+][0-9]+/)\n'; C = 'circle:\n  kind: circle\n  r: !float\nsquare:\n  kind: square\n  side: !float\n'
    star = [('a:\n  !**: !int\n--- !a\n5\n', 5), ('a:\n  !**: !int\n--- !a\n[1, [2]]\n', [1, [2]]), ('a:\n  x?: !str\n  !**: !int\n--- !a\n5\n', 5),
            ('a:\n  !**: !int\n--- !a\n{}\n', {}), ('a: {!**: !int}\n--- !a\n{x: 1}\n', {'x': 1}), ('a:\n  !**:\n    n: !int\n--- !a\n[[{n: 1}]]\n', [[{'n': 1}]]),
            ('a:\n  !**:\n    n: !int\n--- !a\nm: 5\n', {'m': '5'}), ('a:\n  !**:\n    n: !int\n--- !a\n{}\n', {}), ('a:\n  !**:\n    n?: !int\n--- !a\nn:\n', {'n': None}),
            ('a:\n  !**:\n    ports: [!int, ...]\n--- !a\nx: {ports: [1]}\n', {'x': {'ports': [1]}}),
            ('a:\n  !**:\n    db:\n      host: !str\n--- !a\nx: {db: {host: h, more: 1}}\n', {'x': {'db': {'host': 'h', 'more': '1'}}}),
            ('a:\n  x: !any\n  !**: !int\n--- !a\nx: {z: 1}\ny: 2\n', {'x': {'z': '1'}, 'y': 2}), ('a:\n  !**: !any\n--- !a\nx: 1\n', {'x': '1'}),
            ('a:\n  m:\n    !str(/ts_.*/): !str\n  !**:\n    !str(/ts_.*/): !date\n--- !a\nm: {ts_x: hello}\nts_y: 2026-11-06\n', {'m': {'ts_x': 'hello'}, 'ts_y': '2026-11-06'}),
            ('a:\n  !**:\n    !str(/ts_.*/): !date\n  m:\n    ts_x: !str\n--- !a\nm: {ts_x: hello, ts_y: 2026-11-06}\n', {'m': {'ts_x': 'hello', 'ts_y': '2026-11-06'}}),
            ('a:\n  !**: !int\n  b:\n    !**: !bool\n--- !a\nx: 1\nb: {y: true}\n', {'x': 1, 'b': {'y': True}}),
            ('a:\n  !**:\n    n: !int\n  b:\n    !**: !str\n--- !a\nn: 1\nb: {n: 1}\n', {'n': 1, 'b': {'n': '1'}}),
            ('rules:\n  n: !int\na:\n  !**:\n    <<: *rules\n    m: !bool\n--- !a\nx: {n: 1, m: true}\n', {'x': {'n': 1, 'm': True}}),
            ('rules:\n  n: !int\na:\n  !**: *rules\n--- !a\nx: {n: 1}\n', {'x': {'n': 1}}),
            ('addr:\n  name: !str\na:\n  home: !addr\n  !**: !int\n--- !a\nhome: {name: x, floor: 3}\n', {'home': {'name': 'x', 'floor': 3}}),
            ('"*": !int\na:\n  "*": !int\n--- !a\n"*": 5\n', {'*': 5}), ('a:\n  "!*": !int\n--- !a\n"!*": 5\n', {'!*': 5}),
            ('d:\n  n: 1\na:\n  !**:\n    n: !int\n--- !a\nx: *d\n', {'x': {'n': 1}}), ('d:\n  n: 1\na:\n  !**:\n    n: !int\n--- !a\n<<: *d\nm: 2\n', {'n': 1, 'm': '2'}),
            (C + 'u: !circle | !square\na:\n  s: !u\n  !**: !str\n--- !a\ns: {kind: square, side: 2, note: x}\n', {'s': {'kind': 'square', 'side': 2.0, 'note': 'x'}}),
            (S + 'a:\n  !**: !signed | !str\nl: [!a, ...]\n--- !l\n- +5\n- {x: -3}\n', [5, {'x': -3}]),
            ('m:\n  x: !str\na:\n  s: [!m, ...]\n  !**: !int\n--- !a\ns: [{x: a, y: 1}]\n', {'s': [{'x': 'a', 'y': 1}]})]
    star += [('a:\n  !*: !int\n--- !a\nx: 1\ny: 2\n', {'x': 1, 'y': 2}), ('a:\n  n: !str\n  !str(/X_.*/): !str\n  !*: !int\n--- !a\nn: 1\nX_a: 2\nz: 3\n', {'n': '1', 'X_a': '2', 'z': 3}), ('a:\n  !*: !int\n  !str(/X_.*/): !str\n--- !a\nX_a: 2\nz: 3\n', {'X_a': '2', 'z': 3}), ('a:\n  !*:\n    x: !int\n--- !a\nk: {x: 1}\n', {'k': {'x': 1}}), ('a:\n  !*: [!int, ...]\n--- !a\nk: [1]\n', {'k': [1]}), ('a:\n  !*: !int\n  !**: !str\n--- !a\nx: 1\n', {'x': 1}), ('m:\n  n: !int\n  !*: !bool\na:\n  s: !m\n  !**: !str\n--- !a\ns: {n: 1, z: true}\nq: 1\n', {'s': {'n': 1, 'z': True}, 'q': '1'}), ('p:\n  k: a\n  !*: !int\nq:\n  k: b\nu: !p | !q\n--- !u\nk: a\nz: 1\n', {'k': 'a', 'z': 1}), ('a:\n  "!**": !int\n--- !a\n"!**": 5\n', {'!**': 5})]
    for t, w in star:
        try: got = typed('--- &\n' + t)[0]; f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', repr(t), got)
        except REFUSED as e: f += 1; print('REFUSED', repr(t), e)
    notstar = ['a:\n  !**: !int\n--- !a\nx: y\n', 'a:\n  x: !str\n  !**: !int\n--- !a\n5\n', 'a:\n  x: !str\n  !**: !int\n--- !a\ny: 1\n', 'j:\n  !**: !int\nu: !j | !bool\n--- !u\n5\n',
               'j:\n  !**: !int\nu: !j | !bool\n--- !u\n[1]\n', 'a:\n  !**:\n    n: !int\n--- !a\nn:\n', 'a:\n  !**:\n    n: !int\n--- !a\nx: {y: [{n: a}]}\n', 'a:\n  !**:\n    ports: [!int, ...]\n--- !a\nports: 1\n',
               'a:\n  !**:\n    !str(/ts_.*/): !date\n--- !a\nts_x: soon\n', 'a:\n  !**: !int\n  b:\n    !**: !bool\n--- !a\nb: {y: 1}\n', 'a:\n  !**: !int\n  b:\n    c: !str\n--- !a\nb: {c: x, d: y}\n',
               'a:\n  "!*": !int\n--- !a\nx: 5\n', 'a:\n  "*": !int\n--- !a\nx: 5\n', 'addr:\n  name: !str\na:\n  !**: !int\n  home: !addr\n--- !addr\nname: x\nfloor: 3\n', 'a:\n  b:\n    !**: !int\n--- !a\nb: {x: 1}\nc: 2\n',
               'p:\n  x: !int\nq:\n  x: !int\n  z: !int\nu: !p | !q\na:\n  s: !u\n  !**: !str\n--- !a\ns: {x: 1, z: 2}\n', C + 'u: !circle | !square\na:\n  s: !u\n  !**: !str\n--- !a\ns: {kind: oval}\n']
    notstar += ['a:\n  !*: !int\n--- !a\nx: {y: 1}\n', 'a:\n  !*: !int\n--- !a\n5\n', 'a:\n  !*: !int\n--- !a\n[1]\n', 'a:\n  !*: !int\n--- !a\nx: y\n', 'a:\n  "!**": !int\n--- !a\nx: 5\n']
    for t in notstar:
        try: typed('--- &\n' + t); f += 1; print('NOT REFUSED', repr(t))
        except REFUSED: pass
    badstar = ['a:\n  !**:\n    !**: !int', 'a:\n  !ts_*: !date', 'a:\n  !***: !int', 'a:\n  !*: !stirng', 'a:\n  !**:\n    !*: [!int, ...]', 'a:\n  !**: [!int, ...]', 'a:\n  !**: !b\nb:\n  x: !int', 'a:\n  !**: !int | !b\nb:\n  x: !int', 'a:\n  !**: !a', 'a:\n  !**:\n    !*:\n      n: !int', 'a:\n  !**: !stirng', 'a:\n  !**:\n    n: !stirng', 'a:\n  !**:\n    !stirng: !int', 'a:\n  !**:\n    !str(/(a{1000}){1000}/): !int', 'a:\n  !**: !int\n  !**: !str', 'a:\n  !**:\n    !str: !stirng', 'a:\n  !**:\n    !str(/a{400}/): !int\n    !str(/b{400}/): !int\n    !str(/c{400}/): !int']
    for t in badstar:
        try: typed('--- &\n' + t + '\n'); f += 1; print('SCHEMA NOT REFUSED', t)
        except REFUSED: pass
    # Publishing: a name holding a hash, which only an application that asks looks up.
    Y = b'%YAML 2.0\n--- &\naddress:\n  street: !str\n  floor?: !int\n'; h = hashlib.sha256(Y).hexdigest()[:40]
    def yes(b): return hashlib.sha256(b).hexdigest()[:40], b
    D = f'--- !tabcomputing.com/address/v1/{h}.yes\nstreet: a\nfloor: 3\n'; T = {'street': 'a', 'floor': 3}; U = {'street': 'a', 'floor': '3'}
    Q = dict([yes(b'%YAML 2.0\n--- &\na: !int\nb: !str\n')]); q = next(iter(Q))
    W = dict([yes(b'%YAML 2.0\n--- &\na: !int\n---\n1\n')]); w = next(iter(W))
    pub = [(D, {h: Y}, None, T), (D, None, None, U), (D.replace('tabcomputing.com/address/v1', 'mirror.example'), {h: Y}, None, T),
           (D.replace(h, h.upper()), {h: Y}, None, U), (D.replace(h + '.yes', h[:39] + '.yes'), {h: Y}, None, U), (D.replace(f'tabcomputing.com/address/v1/{h}', h), {h: Y}, None, U),
           ('--- !tabcomputing.com/address/v1\nstreet: a\n', {}, None, {'street': 'a'}), (f'--- !x.example/{q}.yes\nz\n', Q, None, 'z'),
           ('--- &\naddress: !int\n' + D, {h: Y}, None, T), (D, {h: Y}, ('--- &\nj:\n  !**: !str\n', 'j'), T), (D, None, ('--- &\nj:\n  !**: !str\n', 'j'), U)]
    for t, st, ap, w_ in pub:
        try: got = typed(t, ap, store=st)[0]; f += 0 if same(got, w_) else 1; same(got, w_) or print('DIFFERS', repr(t), got)
        except REFUSED as e: f += 1; print('REFUSED', repr(t), e)
    notpub = [(D, {h: Y + b' '}), (D, {}), (D, {h: Y[:-1]}), (f'--- !x.example/{w}.yes\n1\n', W), (f'--- !x.example/{q}.yes\n1\nnot: a scalar\n', Q)]
    for t, st in notpub:
        try: typed(t, store=st); f += 1; print('NOT REFUSED', repr(t))
        except REFUSED: pass
    Z = re.search(r'```yaml\n(%YAML 2\.0\n--- &\naddress:.*?)```', spec, re.S)
    if Z and hashlib.sha256(Z[1].encode('utf-8')).hexdigest()[:40] + '.yes' not in spec: f += 1; print('THE SPEC NAMES THE WRONG HASH')
    doubling = lambda n: '--- &\n' + ''.join(f'a{i}: !a{i+1} | !a{i+1}\n' for i in range(n)) + f'a{n}: !int\n--- !a0\n1\n'
    f += 0 if typed(doubling(10)) == [1] else 1
    try: typed(doubling(200)); f += 1; print('NOT REFUSED: 200 doublings')
    except SchemaError: pass
    # Reached entries, and what isn't reached.
    reach = [('--- &\na.example/job:\n  retries: !int\n--- !a.example/job\nretries: 3\n', [{'retries': '3'}]), ('--- &\na: !b\nb: !int\n--- !a\n1\n...\n--- &\nb: !bool\n--- !b\ntrue\n', [1, True]), ('--- &\nbad: !stirng\ngood: !int\n--- !good\n1\n', [1]), ('--- &\na: !int\n--- !a\n1\n--- &\nb: !bool\n--- !b\ntrue\n', [1, True])]
    for t, w in reach:
        try: got = typed(t); f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', repr(t), got)
        except REFUSED as e: f += 1; print('REFUSED', repr(t), e)
    # Numbers: the number written, or a refusal.
    N = '--- &\nf: !float\nd: !decimal\ni: !int\nu: !float | !str\nw: !int | !float\nc: !decimal(0..100)\nq: !float(..3.4e38)\nv: !int(0..18446744073709551615)\n'
    nums = [('f', '0.1', 0.1, 0), ('f', '0.10000000000000001', 0.1, 0), ('f', '0.30000000000000004', 0.30000000000000004, 0), ('f', '1e23', 1e23, 0), ('f', '1.10', 1.1, 0), ('f', '100', 100.0, 0), ('f', '1.7976931348623157e308', 1.7976931348623157e308, 0), ('f', '5e-324', 5e-324, 0), ('f', '0', 0.0, 0), ('f', '0.000', 0.0, 0), ('f', '3.14159265358979323846', 3.141592653589793, 1), ('f', '1.0000076293945313', 1.0000076293945313, 0), ('f', '1.0000076293945312', 1.0000076293945312, 0), ('f', '1.0000076293945314', 1.0000076293945314, 1), ('f', '-1.0000076293945313', -1.0000076293945313, 0), ('f', '1.234567890123e-320', 1.234567890123e-320, 1), ('f', '2.2250738585072014e-308', 2.2250738585072014e-308, 0), ('f', '49954322897937359e-24', 4.995432289793736e-08, 1), ('f', '1e-999', 0.0, 1), ('d', '19.99', 19.99, 0), ('d', '3.14159265358979323846', '3.14159265358979323846', 1), ('d', '1e999999999', '1e999999999', 1), ('i', '340282366920938463463374607431768211456', 2**128, 0), ('u', '"1e999"', '1e999', 0), ('u', '1.5', 1.5, 0), ('w', '3', 3, 0), ('w', '3.5', 3.5, 0), ('c', '100', 100, 0), ('q', '3.4e38', 3.4e38, 0), ('v', '18446744073709551615', 2**64 - 1, 0)]
    for k, v, w, acc in nums:
        try: got = typed(N + f'--- !{k}\n{v}\n', accept=bool(acc))[0]; f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', k, v, got)
        except REFUSED as e: f += 1; print('REFUSED', k, v, e)
    nope = [('f', '3.14159265358979323846', 0), ('f', '1.0000076293945314', 0), ('f', '1.234567890123e-320', 0), ('f', '49954322897937359e-24', 0), ('f', '9007199254740993.0', 0), ('f', '1e999', 0), ('f', '1e999', 1), ('f', '1e-999', 0), ('u', '1e999', 0), ('u', '1e999', 1), ('u', '3.14159265358979323846', 0), ('d', '"19.99"', 0), ('c', '100.01', 0), ('q', '3.5e38', 0), ('v', '18446744073709551616', 0), ('v', '-1', 0)]
    for k, v, acc in nope:
        try: typed(N + f'--- !{k}\n{v}\n', accept=bool(acc)); f += 1; print('NOT REFUSED', k, v)
        except REFUSED: pass
    fulls = [('a: !str\n', 'a', 1), ('a: !int | x\n', 'a', 2), ('big: !int | !str\na: !big | x\n', 'a', 6), ('m:\n  x: !int\n  y?: !str\nu: !m | !int\n', 'u', 10), ('a: !str(/ab{3}/)\n', 'a', 4), ('a: !b | !b\nb: !int\n', 'a', 5), ('a: [!int, ...]\n', 'a', 2), ('a:\n  !**:\n    n: !int\n    !str(/x/): !int\n    !*: !str\n', 'a', 8), ('a:\n  n: !int\n  !*: !str\n', 'a', 5), ('a:\n  !**: !int\n', 'a', 3), ('a: !b\nb: !c\nc: !str\n', 'a', 6)]
    for t, root, n in fulls:
        tb = read('%YAML 2.0\n--- &\n' + t).table
        try:
            Schema(tb, root, limit=n)
            try: Schema(tb, root, limit=n - 1); f += 1; print('NOT REFUSED AT', n - 1, repr(t))
            except SchemaError: pass
        except SchemaError as e: f += 1; print('REFUSED AT', n, repr(t), e)
    chain = '%YAML 2.0\n--- &\n' + ''.join(f'a{i}: !a{i + 1} | !a{i + 2}\n' for i in range(60)) + 'a60: !str\na61: !int\n'
    try: Schema(read(chain).table, 'a0'); f += 1; print('NOT REFUSED: a chain that doubles')
    except SchemaError: pass
    wide = '%YAML 2.0\n--- &\nbig: !str(/a{1022}/)\nr:\n' + ''.join(f'  k{i}: !a{i}\n' for i in range(2000)) + ''.join(f'a{i}: !big | !int\n' for i in range(2000))
    try:
        Schema(read(wide).table, 'r')
        try: Schema(read(wide).table, 'r', limit=2000000); f += 1; print('NOT REFUSED: many unions at the ceiling')
        except SchemaError: pass
    except SchemaError as e: f += 1; print('REFUSED', e)
    try: typed('%YAML 2.0\n--- &\na: !int | !str\n--- !a\n1\n', limit=1); f += 1; print('NOT REFUSED: a stamp past the limit')
    except SchemaError: pass
    emptyseq = ['[""]', '[a]', 'abc', '{}']
    for v in emptyseq:
        try: typed(f'%YAML 2.0\n--- &\nu: !int | []\n--- !u\n{v}\n'); f += 1; print('NOT REFUSED', v)
        except REFUSED: pass
    print(f'edge cases: {len(good) + len(emptyseq) + 2 * len(fulls) + 5 + len(no) + len(schemas) + len(ints) + len(notints) + 1 + len(forms) + 1 + len(says) + 2 + len(unions) + len(star) + len(notstar) + len(badstar) + len(pub) + len(notpub) + 1 + 1 + len(reach) + len(nums) + len(nope)} run, {f} fail')
    sys.exit(1 if bad or f else 0)
