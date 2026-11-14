"""Test spec/yaml-easy-schema.md: a throwaway checker written from its text. Not a reference.

    python3 -I schemacheck.py SPEC

Reads every example with the grammar in draftcheck.py, types each document whose local name
is in the table, and compares the result with the example's JSON. Then runs edge cases.
"""
import base64, binascii, datetime, hashlib, json, math, os, re, sys, unicodedata
from decimal import Decimal, InvalidOperation
from fractions import Fraction
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
    """A value a parser can't deliver. It refuses the document, and isn't a failed match."""
class Written(str):
    """A !decimal whose exponent Python's Decimal can't hold, delivered as written (section 4.4)."""
def nearest(d):
    """d in binary64, exactly: the nearest, the even one on a tie. None if it is too large to hold.
    Exact arithmetic, to check that float() rounds as section 4.4 says."""
    p, low, top = 53, -1074, 1024
    if d == 0: return Fraction(0)
    if d.adjusted() > 5000: return None
    if d.adjusted() < -5000: return Fraction(0)
    x = abs(Fraction(d))
    e = x.numerator.bit_length() - x.denominator.bit_length()
    if Fraction(2) ** e > x: e -= 1
    unit = Fraction(2) ** max(e - p + 1, low)
    n = x / unit; k = n.numerator // n.denominator; r = n - k
    if r > Fraction(1, 2) or (r == Fraction(1, 2) and k % 2): k += 1
    v = k * unit
    if v >= Fraction(2) ** top: return None
    return v if d > 0 else -v
def dec(t):
    """t as a Decimal, to test a limit on. Decimal holds an exponent to about 10^18. Past that, a
    stand-in that compares with a limit as t does: 0 if its digits are, and otherwise infinity or
    Decimal's smallest value above 0, with t's sign."""
    try: return Decimal(t)
    except InvalidOperation:
        m = re.fullmatch(r'([-+]?)([0-9.]*)[eE]([-+]?)[0-9]+', t)
        if not m[2].strip('0.'): return Decimal(m[1] + '0')
        return Decimal(m[1] + ('1e-1999999999999999997' if m[3] == '-' else 'Infinity'))
def canon(t):
    """Section 4.5: a number a pattern matched, in the standard spelling: no +, no leading zeros, and
    a digit on each side of a point. The digits and exponent are kept, so 100e-2 stays 100e-2."""
    m = re.fullmatch(r'([-+]?)([0-9]*)(?:\.([0-9]*))?([eE][-+]?[0-9]+)?', t)
    return ('-' if m[1] == '-' else '') + (m[2].lstrip('0') or '0') + ('.' + m[3] if m[3] else '') + (m[4] or '')

STD = {'str', 'int', 'bigint', 'float', 'decimal', 'bool', 'null', 'any', 'date', 'datetime', 'binary'}
FLOAT = r'-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?'
INT = r'-?(0|[1-9][0-9]*)'
INTS = ('int', 'bigint')
INTRANGE = (-2 ** 63, 2 ** 64 - 1)  # Section 4.4: !int on every parser.
READINT = r'[-+]?[0-9]+'
READDEC = r'[-+]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][-+]?[0-9]+)?'
DATE = r'([0-9]{4})-([0-9]{2})-([0-9]{2})'
DATETIME = DATE + r'[Tt]([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]+))?(?:[Zz]|([-+])([0-9]{2}):([0-9]{2}))'
# Section 4.8: what this parser holds of a date, as (fraction digits, second 60, year 0000). None holds
# them all, since it delivers the text. A test sets Python's (6, False, False) or JavaScript's (3, False, True).
DATEHOLD = None
def leapyear(y): return (y % 4 == 0 and y % 100 != 0) or y % 400 == 0
def lastday(y, m): return (31, 29 if leapyear(y) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[m - 1]
def days(y, m, d):
    """Days from 1970-01-01 in the proleptic Gregorian calendar, for any year."""
    y -= m <= 2; era = y // 400; yoe = y - era * 400
    doy = (153 * (m - 3 if m > 2 else m + 9) + 2) // 5 + d - 1
    return era * 146097 + yoe * 365 + yoe // 4 - yoe // 100 + doy - 719468
def civil(z):
    z += 719468; era = z // 146097; doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100); mp = (5 * doy + 2) // 153
    m = mp + 3 if mp < 10 else mp - 9
    return yoe + era * 400 + (m <= 2), m, doy - (153 * mp + 2) // 5 + 1
def rfc3339(t, full):
    """RFC 3339 section 5.6, with 5.7's days of the month. A second of 60 is allowed at 23:59 UTC on the
    last day of any month, once the offset is taken off, as section 4.8 proposes. The match, or None."""
    m = re.fullmatch(DATETIME if full else DATE, t)
    if not m: return None
    y, mo, d = (int(x) for x in m.groups()[:3])
    if not (1 <= mo <= 12 and 1 <= d <= lastday(y, mo)): return None
    if not full: return m
    hh, mm, ss = (int(x) for x in m.groups()[3:6])
    oh, om = (int(m[9]), int(m[10])) if m[8] else (0, 0)
    if hh > 23 or mm > 59 or ss > 60 or oh > 23 or om > 59: return None
    if ss == 60:
        utc = days(y, mo, d) * 1440 + hh * 60 + mm - (-1 if m[8] == '-' else 1) * (oh * 60 + om)
        z, rest = divmod(utc, 1440); uy, um, ud = civil(z)
        if rest != 23 * 60 + 59 or ud != lastday(uy, um): return None
    return m
def dated(t, full, cut, path):
    """Section 4.8: the value written, or a refusal if this parser can't hold it. With cut, which only an
    application turns on, a fraction this parser can't hold is cut to the digits it holds, never rounded up."""
    m = rfc3339(t, full)
    if not m: raise ValueError
    if DATEHOLD:
        held, leap, year0 = DATEHOLD
        frac = (m[7] or '') if full else ''
        if cut and len(frac) > held:
            t = t[:m.start(7) - 1] + ('.' + frac[:held] if held else '') + t[m.end(7):]; m = rfc3339(t, full)
        if (full and len(m[7] or '') > held) or (full and int(m[6]) == 60 and not leap) or (int(m[1]) == 0 and not year0):
            raise Cant(f'{path or "/"}: this parser can not hold {t[:40]}')
    return t

TYPENAME = re.compile(r'(?:^|[ \[,])![^ \t()\[\],|/]+$')
def args_end(text, i):
    """Where a type's parentheses, opened at i, end: at the first `/)` once a pattern starts, else at `)`."""
    k = i + 1
    while k < len(text) and text[k] not in '/)': k += 1
    if k >= len(text): raise SchemaError(f'unclosed parentheses: {text}')
    if text[k] == ')': return k + 1
    e = text.find('/)', k + 1)
    if e < 0: raise SchemaError(f'unclosed pattern: {text}')
    return e + 2
def split(text, sep):
    """Split at sep outside brackets and outside a type's parentheses. A `(` elsewhere is literal text."""
    parts, depth, i, b = [], 0, 0, 0
    while i < len(text):
        c = text[i]
        if c == '(' and TYPENAME.search(text, 0, i): i = args_end(text, i); continue
        depth += c == '['; depth -= c == ']'
        if depth == 0 and text.startswith(sep, i):
            parts.append(text[b:i]); i += len(sep); b = i; continue
        i += 1
    return parts + [text[b:]]
CATS = re.compile(r'L[lmotu]?|M[cen]?|N[dlo]?|P[cdefios]?|Z[lps]?|S[ckmo]?|C[cfno]?')
RUNS = {}
def runs(name):
    """The code point ranges of a general category, from this Python's Unicode (16 on 3.14)."""
    if not RUNS:
        cur = None
        for c in range(0x110000):
            g = unicodedata.category(chr(c))
            if cur and cur[0] == g and cur[2] == c - 1: cur[2] = c
            else:
                cur = [g, c, c]; RUNS.setdefault(g, []).append(cur)
    rs = sorted(r[1:] for g, v in RUNS.items() if g == name or (len(name) == 1 and g[0] == name) for r in v)
    out = []
    for lo, hi in rs:
        if out and out[-1][1] == lo - 1: out[-1][1] = hi
        else: out.append([lo, hi])
    return out
def catclass(name, neg=False):
    rs = runs(name)
    if neg:
        comp, at = [], 0
        for lo, hi in rs:
            if lo > at: comp.append([at, lo - 1])
            at = hi + 1
        if at <= 0x10FFFF: comp.append([at, 0x10FFFF])
        rs = comp
    return ''.join(f'\\U{lo:08x}' + (f'-\\U{hi:08x}' if hi > lo else '') for lo, hi in rs)
class Pat:
    """A compiled pattern, with its count as written (section 9)."""
    def __init__(s, rx, count, written): s.rx, s.count, s.written = rx, count, written
    def fullmatch(s, t): return s.rx.fullmatch(t)
SINGLE = '()*+-.?[\\]^nrt{|}'
def iregexp(p, whole):
    """RFC 9485, section 3. Returns the same pattern for Python, and its count."""
    i, n, deep = 0, len(p), 0
    def bad(why='not I-Regexp'): raise SchemaError(f'{why}: {whole}')
    def esc():
        nonlocal i
        c = p[i + 1:i + 2]
        if c in ('p', 'P'):
            m = re.match(r'\\[pP]\{([A-Za-z]*)\}', p[i:])
            if not m or not CATS.fullmatch(m[1]): bad()
            i += len(m[0]); return ('cat', m[1], c == 'P')
        if c and c in SINGLE: i += 2; return ('ch', '\\' + c)
        bad()
    def regexp():
        nonlocal i
        src, cnt = branch()
        while i < n and p[i] == '|':
            i += 1; s2, c2 = branch(); src += '|' + s2; cnt += c2
        return src, cnt
    def branch():
        nonlocal i
        src, cnt = '', 0
        while i < n and p[i] not in '|)':
            s, c = atom(); q, k = quant(); src += s + q; cnt += c * k
        return src, cnt
    def atom():
        nonlocal i, deep
        ch = p[i]
        if ch == '(':
            deep += 1
            if deep > 256: bad('groups nested past 256')
            i += 1; s, c = regexp()
            if i >= n or p[i] != ')': bad()
            i += 1; deep -= 1; return '(?:' + s + ')', c
        if ch == '.': i += 1; return '[^\\n\\r]', 1
        if ch == '[': return cls(), 1
        if ch == '\\':
            e = esc()
            return (('[^' if e[2] else '[') + catclass(e[1]) + ']', 1) if e[0] == 'cat' else (e[1], 1)
        if ch in '^$': bad(f'{ch} outside a class')
        if ch in '*+?{}]': bad()
        i += 1; return re.escape(ch), 1
    def quant():
        nonlocal i
        if i < n and p[i] in '*+?': i += 1; return p[i - 1], 1
        if i < n and p[i] == '{':
            m = re.match(r'\{([0-9]+)(,([0-9]*))?\}', p[i:])
            if not m: bad()
            i += len(m[0]); lo = int(m[1]); hi = lo if m[2] is None else int(m[3]) if m[3] else None
            if hi is not None and hi < lo: bad()
            return m[0], max(lo, 1) if hi is None else hi
        return '', 1
    def one():
        nonlocal i
        ch = p[i]
        if ch == '\\':
            e = esc()
            return e if e[0] == 'cat' else ('ch', e[1])
        if ch in '[]-': bad()
        i += 1; return ('ch', re.escape(ch))
    def cls():
        nonlocal i
        i += 1; neg = p[i:i + 1] == '^'; i += neg; parts = []
        if p[i:i + 1] == '-': parts.append('\\-'); i += 1
        while True:
            if i >= n: bad()
            if p[i] == ']':
                if not parts: bad()
                i += 1; return ('[^' if neg else '[') + ''.join(parts) + ']'
            if p[i] == '-' and p[i + 1:i + 2] == ']': parts.append('\\-'); i += 1; continue
            a = one()
            if a[0] == 'cat': parts.append(catclass(a[1], a[2])); continue
            if p[i:i + 1] == '-' and p[i + 1:i + 2] not in (']', ''):
                i += 1; b = one()
                if b[0] == 'cat': bad()
                parts.append(a[1] + '-' + b[1])
            else: parts.append(a[1])
    src, cnt = regexp()
    if i != n: bad()
    return src, cnt
def pattern(p, whole):
    src, n = iregexp(p, whole)
    try: rx = re.compile(src)
    except re.error: raise SchemaError(f'not I-Regexp: {whole}')
    return ('re', Pat(rx, n, p))
RANGE = r'(-?[0-9]+(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?)?\.\.(-?[0-9]+(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?)?'
PATTERNED = ('str', 'int', 'bigint', 'float', 'decimal', 'null')
def limit(text, name, whole):
    """Sections 4.2 and 4.5 to 4.7: in one pair of parentheses, in this order and at most one of each,
    a precision (decimal only), a range and a pattern, one space between them. A pattern is last, and
    ends at the first `/)`."""
    if name not in PATTERNED: raise SchemaError(f'{whole}: !{name} takes nothing in parentheses')
    i = text.find('/'); head, pat = (text, None) if i < 0 else (text[:i], text[i:])
    if pat is not None:
        if len(pat) < 2 or pat[-1] != '/': raise SchemaError(f'bad pattern: {whole}')
        if head:
            if not head.endswith(' '): raise SchemaError(f'bad limit: {whole}')
            head = head[:-1]
        pat = pattern(pat[1:-1], whole)[1]
    prec = rng = None
    for k, a in enumerate(head.split(' ') if head else []):
        m = re.fullmatch(r'([1-9][0-9]*):(0|[1-9][0-9]*)', a)
        if m and k == 0 and name == 'decimal':
            prec = (int(m[1]), int(m[2]))
            if prec[1] > prec[0]: raise SchemaError(f'a scale larger than the precision: {whole}')
            continue
        m = re.fullmatch(RANGE, a)
        if m and rng is None and (m[1] or m[2]) and name != 'null':
            lo, hi = (None if x is None else dec(x) for x in m.groups())
            if lo is not None and hi is not None and lo > hi: raise SchemaError(f'bad limit: {whole}')
            rng = (lo, hi); continue
        raise SchemaError(f'bad limit: {whole}')
    if not (pat or rng or prec): raise SchemaError(f'bad limit: {whole}')
    return ('args', pat, rng, prec)
def fits(t, p, sc):
    """Section 4.6, on the exact value: at most sc digits after the point and p - sc before it. On the
    text, so an exponent of any size is counted."""
    m = re.fullmatch(r'-?([0-9]+)(?:\.([0-9]+))?(?:[eE]([-+]?[0-9]+))?', t)
    ds = (m[1] + (m[2] or '')).lstrip('0'); e = int(m[3] or 0) - len(m[2] or '')
    if not ds: return True
    n = len(ds.rstrip('0')); e += len(ds) - n
    return max(0, -e) <= sc and n + e <= p - sc
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
    ps = split(text, ' | ')
    for p in ps:
        if p != p.strip(' '): raise SchemaError(f'a part starts or ends with a space: {text!r}')
    alts = [atom(p.strip()) for p in ps]
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
class Rules(tuple):
    """What a `!**` holds. A mapping of rules counts its keys in the full size."""
def rule(x):
    """What `!**` holds: named keys, type keys, and in `!*` a type for every other scalar."""
    if isinstance(x, dict):
        t = to_type(x)
        if t[3] is not None: raise SchemaError('a `!**` holds no `!**`')
        r = Rules((t[1], t[2], t[4])); r.keys = True; return r
    r = Rules(({}, [], to_type(x))); r.keys = False; return r
def strip(v):
    if isinstance(v, dict): return {str(k): strip(x) for k, x in v.items()}
    if isinstance(v, list): return [strip(x) for x in v]
    return str(v)

CEILING = 1024
LIMIT = 64 * 2 ** 20

class Schema:
    def __init__(s, table, root, cut=False, limit=LIMIT, kept=False):
        s.table, s.defs, s.memo, s.seen, s.reached, s.cut = table, {}, {}, set(), {root}, cut
        # Section 11: an interface that keeps references types each node once for each type and nearest
        # `!**`, and adds the node's own size to typed each time. The reader hands back the table's own
        # object for a reference, so a shared node is one object here. CPython shares strings of one
        # character, so two plain one-character scalars count as one node; no test relies on that.
        s.kept, s.limit, s.count, s.done = kept, limit, 0, {}
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
        if t[0] == 'name' and t[2] is not None:
            a = t[2] if isinstance(t[2], tuple) else limit(t[2], t[1], t[3])
            return a[1].count if a[1] else 1
        if t[0] == 'lit': return 1
        if t[0] == 'map':
            n = 1 + len(t[1]) + len(t[2]) + (t[4] is not None)
            if t[3]: n += 1 + (len(t[3][0]) + len(t[3][1]) + (t[3][2] is not None) if t[3].keys else 0)
            return n
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
            if x[0] == 'name' and x[2] and x[2][1]: n += x[2][1].count
            else: n += 1
        if n > CEILING: raise SchemaError(f'a union of {n} positions')
    def walk(s, t):
        if id(t) in s.seen: return
        s.seen.add(id(t)); s.place(t); a = s.alts(t)
        if sum(1 for x in a if x[0] == 'seq') > 1: raise SchemaError('more than one sequence alternative')
        maps = [x for x in a if x[0] == 'map']
        if len(maps) > 1: s.ceiling([y for x in maps for kt, _ in x[2] for y in s.alts(kt)])
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
    def check(s, v):
        s.count, s.done = 0, {}  # Section 11: typed counts the document being typed.
        return s.conv(s.root, v, '')
    def own(s, v):
        """A node's own size, as held counts it: 1, a scalar's bytes, or a mapping's keys. Not what is below."""
        b = lambda x: 1 + len(str(x).encode('utf-8', 'surrogatepass'))
        if isinstance(v, dict): return 1 + sum(b(k) for k in v)
        return 1 if isinstance(v, list) else b(v)
    def kind(s, t):
        """Section 11: each type written in the schema is one type, and a name is its entry's."""
        while t[0] == 'name' and t[1] in s.table and t[2] is None: t = s.get(t[1])
        return id(t)
    def typing(s, key, v, path, work):
        """Once for each node, type and nearest `!**`, adding the node's own size to typed each time."""
        if not s.kept: return work()
        k = (id(v),) + key
        if k in s.done: return s.done[k]
        s.count += s.own(v)
        if s.count > s.limit: raise No(f'{path or "/"}: typed passes the size limit')
        out = s.done[k] = work()
        return out
    def under(s, k, y, path, scope):
        """A key the mapping at this place doesn't name, under the nearest `!**`."""
        fields, rows, _ = scope; p = f'{path}/{k}'
        if k in fields:
            ft, opt = fields[k]
            if opt and y == '' and not isinstance(y, Quoted): return None
            return s.conv(ft, y, p, scope)
        for kt, vt in rows:
            try: s.convert(kt, str(k), path)
            except Bad: continue
            return s.conv(vt, y, p, scope)
        return s.anywhere(y, p, scope)
    def anywhere(s, v, path, scope):
        if not isinstance(v, (dict, list)) and scope[2]: return s.conv(scope[2], v, path, scope)
        return s.typing(('**', id(scope)), v, path, lambda: s.below(v, path, scope))
    def below(s, v, path, scope):
        if isinstance(v, dict): return {str(k): s.under(k, y, path, scope) for k, y in v.items()}
        if isinstance(v, list): return [s.anywhere(y, f'{path}/{i}', scope) for i, y in enumerate(v)]
        return strip(v)
    def conv(s, t, v, path, scope=None):
        return s.typing((s.kind(t), id(scope)), v, path, lambda: s.convert(t, v, path, scope))
    def convert(s, t, v, path, scope=None):
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
        for x in [x for x in a if x not in anys] + anys:
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
                try: s.convert(kt, str(k), '')
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
                try: s.convert(kt, str(k), path)
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
        if name in ('int', 'bigint', 'float', 'decimal', 'bool', 'null') and isinstance(v, Quoted): raise Bad(path, f'not plain, so not {name}')
        t = str(v); out = None; pat = lim[1] if lim else None
        def outside(n):
            if lim and lim[2]:
                lo, hi = lim[2]
                if (lo is not None and n < lo) or (hi is not None and n > hi): raise Bad(path, f'{t[:40]!r} is out of range')
        if pat and name != 'str':
            # Section 4.5: the pattern replaces the spelling, and the type reads what it matched.
            if not pat.fullmatch(t): raise Bad(path, f'{t[:40]!r} does not match')
            if name == 'null': return None
            if not re.fullmatch(READINT if name in INTS else READDEC, t):
                raise Cant(f'{path or "/"}: {t[:40]!r} matched, and is not ' + ('an integer' if name in INTS else 'a number'))
            t = str(int(t)) if name in INTS else canon(t)
        try:
            if name == 'str': out = t
            elif name == 'bool' and t in ('true', 'false'): out = t == 'true'
            elif name == 'null' and t == 'null': out = None
            elif name in INTS and re.fullmatch(INT, t):
                # Section 4.4: a limit first, on the number as written; then outside !int's range refuses
                # the document. A parser delivers !bigint's digits unconverted; this checker converts, to
                # compare with JSON.
                out = int(t); outside(out)
                if name == 'int' and not INTRANGE[0] <= out <= INTRANGE[1]: raise Cant(f'{path or "/"}: {t[:40]} is outside !int')
            elif name == 'float' and re.fullmatch(FLOAT, t):
                # Section 4.4: a limit first, on the number as written; then the nearest binary64, the
                # even one on a tie, which is what Python's float() gives. One too large for binary64
                # refuses the document, and one too small for it is 0, with its sign.
                outside(dec(t)); out = float(t)
                if math.isinf(out): raise Cant(f'{path or "/"}: {t[:40]} is too large for binary64')
            elif name == 'decimal' and re.fullmatch(FLOAT, t):
                # Section 4.4: the digits and exponent as written, never expanded.
                try: out = Decimal(t)
                except InvalidOperation: out = Written(t)
            elif name in ('date', 'datetime'): out = dated(t, name == 'datetime', s.cut, path)
            elif name == 'binary':
                t = t.replace('\n', '')
                if base64.b64encode(base64.b64decode(t.encode('ascii'), validate=True)).decode() != t: raise ValueError
                out = t
            else: raise ValueError
        except (ValueError, binascii.Error, UnicodeEncodeError): raise Bad(path, f'expected {name}, got {t[:40]!r}')
        if pat and name == 'str' and not pat.fullmatch(t): raise Bad(path, f'{t[:40]!r} does not match')
        if lim and lim[3] and not fits(t, *lim[3]): raise Bad(path, f'{t[:40]!r} has too many digits for {lim[3][0]}:{lim[3][1]}')
        if lim and lim[2]:
            lo, hi = lim[2]; n = len(t) if name == 'str' else dec(t) if name in ('float', 'decimal') else out
            if (lo is not None and n < lo) or (hi is not None and n > hi): raise Bad(path, f'{t[:40]!r} is out of range')
        return out

PUB = re.compile(r'[^/#]+(?:/[^/#]+)*/([^/#]+)\.yes#sha256=([0-9a-f]{64})')
def published(name, store, cut, limit=LIMIT, keep=False):
    """Section 3.1. The store is what an application can get, by hash, from anywhere."""
    root, h = PUB.fullmatch(name).groups(); b = store.get(h)
    if b is None: raise Cant(f'{name}: the file is not to be had')
    if hashlib.sha256(b).hexdigest() != h: raise Cant(f'{name}: the file does not hash to its name')
    text = b.decode('utf-8'); r = read(text, limit)
    marks = re.findall(r'^(?:---|\.\.\.)(?=[ \t\n]|$).*', text, re.M)
    if r.docs or not r.table or len(marks) != 1 or not marks[0].startswith('--- &'):
        raise SchemaError(f'{name}: a published schema is one table and nothing else')
    # Section 3.1: the root is the entry named like the file.
    if root not in r.table: raise SchemaError(f'{name}: the file has no entry {root}')
    return Schema(r.table, root, cut, limit, keep)
def typed(stream, app=None, store=None, limit=LIMIT, cut=False, keep=False):
    """Type each stamped document by the file's table, others by the application's schema.
    With neither they stay strings. An application's schema is (schema text, root). A store
    means the application looks published names up. Cut is an application cutting a time to what this parser holds (sections 3 and 4.8). Keep
    types as an interface that keeps references does, counting typed (section 11)."""
    r = read(stream); out = []; reached = {}; live = None
    # Section 3: a schema from outside the stream is a stream too, read under part 1's limit.
    own = None if app is None else Schema(read(app[0], limit).table, app[1], cut, limit, keep)
    for (name, v), (table, obj) in zip(r.docs, getattr(r, 'snaps', [])):
        if obj is not live: reached, live = {}, obj
        for k, e in reached.items():
            if table.get(k) is not e: raise SchemaError(f'{k} was replaced after a type reached it')
        if name and '/' not in name and name in table:
            sc = Schema(table, name, cut, limit, keep); out.append(sc.check(v))
            reached.update((k, table[k]) for k in sc.reached)
        elif store is not None and name and PUB.fullmatch(name): out.append(published(name, store, cut, limit, keep).check(v))
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
    if isinstance(a, Written) or isinstance(b, Written): return type(a) is type(b) and a == b
    if isinstance(a, Decimal): return a == Decimal(repr(b) if isinstance(b, float) else str(b))
    if isinstance(a, float) and isinstance(b, Decimal): return a == float(b)  # An example's JSON, read exactly.
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
            d = json.JSONDecoder(parse_float=Decimal); t = blocks[i + 1][2].strip(); want = []; k = 0
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
    schemas = ['"my type": !int\na: !my type', '"my\ttype": !int\na: !my\ttype', 'a: !int | [ ]', 'a: !int | [!int, ]', 'a: !int | [, !int]', 'a: !int | [...]', 'a: !nope', 'a: !str(1,2)', 'a: !bool(0..1)', 'a: !bool(/x/)', 'a: !date(/x/)', 'a: !datetime(/x/)', 'a: !binary(/x/)', 'a: !any(/x/)', 'a: !int(/(1{1000}){1000}/)', 'a: !int(/^1/)', 'a: !int(5..1)', 'a: !a', 'a: !b\nb: !a', 'a: !str(/^x/)', 'a: !str(/x$/)', 'a: !str(/\\d+/)', 'a: !str(/(?=x)/)', 'a: [!a, !b] | [!c]', 'a: !x(1..)\nx: !str', 'a: !str | {b: c}', 'a: [...]', 'a: !a/b', 'a: !str(/x', 'a: [!int(0,100), ...]', 'a: {b: !int(0,100)}', 'a: [!str(/[a-z]+/), ...]', 'a: [!str(/(a|b),c/), ...]', 'a: [!str(/[0-9]{2}/), ...]', 'a: {b: !str(/[a-z]+/)}', 'a: {!str(/[a-z]+/): !int}', 'a: !str(/x #y/)', 'a: !str(/x: y/)', 'a: !int | "none"', "a: !int | 'none'", 'a: !b | !int\nb: !a | !str', 'a: !str(/(a{1000}){1000}/)', 'a: !str(/a{1025}/)', 'a: !str(/a{513}/) | !str(/b{512}/)', 'a:\n  !str(/a{513}/): !int\n  !str(/b{512}/): !int',
               'a: !int(/[0-9]+/ 0..100)', 'a: !int(0..1 5..9)', 'a: !int(5:2)', 'a: !float(5:2)', 'a: !str(5:2)', 'a: !decimal(0..1 5:2)',
               'a: !decimal(2:5)', 'a: !decimal(0:0)', 'a: !decimal(05:2)', 'a: !decimal(5:02)', 'a: !decimal(5: 2)', 'a: !decimal(5,2)', 'a: !decimal(5:2 5:2)',
               'a: !decimal(5:2 /x/ 0..1)', 'a: !int(0..100  /x/)', 'a: !int(0..100/x/)', 'a: !int( 0..100)', 'a: !int(0..100 )', 'a: !null(0..1 /x/)',
               'a: !null(0..1)', 'a: !int()', 'a: [!decimal(5,2), ...]', 'a: {b: !decimal(5,2)}', 'a: !decimal(5:2 /^x/)', 'a: !float(/x/ 0..1)']
    for t in schemas:
        try: typed('--- &\n' + t + '\n'); f += 1; print('SCHEMA NOT REFUSED', t)
        except REFUSED: pass
    # A pattern on !int: it replaces the spelling, reads base 10, and a claim it can't read refuses.
    I = '--- &\nq: !int(/[-+][0-9]+/)\nw: !int(/[-+]?[0-9]+/)\nu: !q | !str\nh: !int(/0x[0-9a-f]+/)\nv: !h | !str\nk: !int(/[0-9_]+/)\nar: !int(/[٠-٩]+/)\nfirst: !str | !q\nlit: !q | never\nsome: !int(/[0-9]*/)\no:\n  a: !some\nmk:\n  !q: !str\nby: !bigint | !str\nbyi: !int | !str\n'
    ints = [('q', '+5', 5), ('q', '-3', -3), ('q', '+0', 0), ('q', '-0', 0), ('q', '+007', 7), ('w', '5', 5), ('w', '007', 7), ('w', '+5', 5),
                    ('u', '+5', 5), ('u', '+5x', '+5x'), ('u', 'x+5', 'x+5'), ('u', '5', '5'), ('u', '"+5"', '+5'), ('u', "'+5'", '+5'), ('u', 'x', 'x'), ('u', '|\n  +5', '+5\n'), ('v', 'x', 'x'),
                    ('first', '+5', '+5'), ('lit', 'never', 'never'), ('lit', '+5', 5), ('k', '1000', 1000), ('mk', '+5: a\n"-3": b', {'+5': 'a', '-3': 'b'}),
                    ('by', '9' * 5000, int('9' * 5000))]
    for k, v, w in ints:
        try: got = typed(I + f'--- !{k}\n{v}\n')[0]; f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', k, v, got)
        except REFUSED as e: f += 1; print('REFUSED', k, v, e)
    notints = [('q', '5'), ('q', '"+5"'), ('q', "'+5'"), ('q', '|\n  +5'), ('q', '+5x'), ('q', 'x+5'), ('q', '+'), ('q', '[+5]'), ('h', '0x1f'), ('v', '0x1f'),
                 ('k', '1_000'), ('ar', '٣'), ('byi', '9' * 5000), ('o', 'a:'), ('lit', '5'), ('mk', '5: a')]
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
    Y = b'%YAML 2.0\n--- &\naddress:\n  street: !str\n  floor?: !int\n'; h = hashlib.sha256(Y).hexdigest()
    def yes(b): return hashlib.sha256(b).hexdigest(), b
    D = f'--- !tabcomputing.com/address/v1/address.yes#sha256={h}\nstreet: a\nfloor: 3\n'; T = {'street': 'a', 'floor': 3}; U = {'street': 'a', 'floor': '3'}
    Q = dict([yes(b'%YAML 2.0\n--- &\na: !int\nb: !str\n')]); q = next(iter(Q))
    W = dict([yes(b'%YAML 2.0\n--- &\na: !int\n---\n1\n')]); w = next(iter(W))
    pub = [(D, {h: Y}, None, T), (D, None, None, U), (D.replace('tabcomputing.com/address/v1', 'mirror.example'), {h: Y}, None, T),
           (D.replace(h, h.upper()), {h: Y}, None, U), (D.replace(h, h[:63]), {h: Y}, None, U), (D.replace('tabcomputing.com/address/v1/', ''), {h: Y}, None, U),
           (D.replace('#sha256=', '#sha512='), {h: Y}, None, U), (D.replace('address.yes', 'address'), {h: Y}, None, U),
           ('--- !tabcomputing.com/address/v1\nstreet: a\n', {}, None, {'street': 'a'}), (f'--- !x.example/b.yes#sha256={q}\nz\n', Q, None, 'z'), (f'--- !x.example/a.yes#sha256={q}\n1\n', Q, None, 1),
           ('--- &\naddress: !int\n' + D, {h: Y}, None, T), (D, {h: Y}, ('--- &\nj:\n  !**: !str\n', 'j'), T), (D, None, ('--- &\nj:\n  !**: !str\n', 'j'), U)]
    for t, st, ap, w_ in pub:
        try: got = typed(t, ap, store=st)[0]; f += 0 if same(got, w_) else 1; same(got, w_) or print('DIFFERS', repr(t), got)
        except REFUSED as e: f += 1; print('REFUSED', repr(t), e)
    notpub = [(D, {h: Y + b' '}), (D, {}), (D, {h: Y[:-1]}), (f'--- !x.example/a.yes#sha256={w}\n1\n', W), (f'--- !x.example/b.yes#sha256={q}\n1\nnot: a scalar\n', Q),
              (f'--- !x.example/c.yes#sha256={q}\nz\n', Q), (f'--- !x.example/b.yes#sha256={q}\n[z]\n', Q)]
    for t, st in notpub:
        try: typed(t, store=st); f += 1; print('NOT REFUSED', repr(t))
        except REFUSED: pass
    Z = re.search(r'### 3\.1 .*?```yaml\n(%YAML 2\.0\n--- &\n.*?)```', spec, re.S)
    if not Z or 'address.yes#sha256=' + hashlib.sha256(Z[1].encode('utf-8')).hexdigest() not in spec: f += 1; print('THE SPEC NAMES THE WRONG HASH')
    doubling = lambda n: '--- &\n' + ''.join(f'a{i}: !a{i+1} | !a{i+1}\n' for i in range(n)) + f'a{n}: !int\n--- !a0\n1\n'
    f += 0 if typed(doubling(10)) == [1] else 1
    try: typed(doubling(200)); f += 1; print('NOT REFUSED: 200 doublings')
    except SchemaError: pass
    # Reached entries, and what isn't reached.
    reach = [('--- &\na.example/job:\n  retries: !int\n--- !a.example/job\nretries: 3\n', [{'retries': '3'}]), ('--- &\na: !b\nb: !int\n--- !a\n1\n...\n--- &\nb: !bool\n--- !b\ntrue\n', [1, True]), ('--- &\nbad: !stirng\ngood: !int\n--- !good\n1\n', [1]), ('--- &\na: !int\n--- !a\n1\n--- &\nb: !bool\n--- !b\ntrue\n', [1, True])]
    for t, w in reach:
        try: got = typed(t); f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', repr(t), got)
        except REFUSED as e: f += 1; print('REFUSED', repr(t), e)
    # Numbers: the number written, the nearest binary64 for !float, or a refusal.
    N = '--- &\nf: !float\nd: !decimal\ni: !int\nb: !bigint\nbu: !bigint(0..) | !str\nu: !float | !str\nw: !int | !float\nc: !decimal(0..100)\nq: !float(..3.4e38)\nv: !int(0..18446744073709551615)\n'
    TOP = 2 ** 1024 - 2 ** 970  # Halfway between binary64's largest value and 2^1024.
    nums = [('f', '1.00000000000000011102230246251565404236316680908203125', 1.0), ('f', '1.00000000000000033306690738754696212708950042724609375', 1.0000000000000004),
            ('f', '1.000000000000000111022302462515654042363166809082031250000001', 1.0000000000000002), ('f', '0.1', 0.1), ('f', '0.10000000000000001', 0.1),
            ('f', '0.30000000000000004', 0.30000000000000004), ('f', '1e23', 1e23), ('f', '1.10', 1.1), ('f', '100', 100.0), ('f', '1.7976931348623157e308', 1.7976931348623157e308),
            ('f', str(TOP - 1), 1.7976931348623157e308), ('f', '5e-324', 5e-324), ('f', '0', 0.0), ('f', '0.000', 0.0), ('f', '3.14159265358979323846', 3.141592653589793),
            ('f', '1.0000076293945314', 1.0000076293945314), ('f', '1.234567890123e-320', 1.234567890123e-320), ('f', '49954322897937359e-24', 4.995432289793736e-08),
            ('f', '9007199254740993', 9007199254740992.0), ('f', '9007199254740995', 9007199254740996.0), ('f', '1e-999', 0.0), ('f', '16777217', 16777217.0),
            ('d', '19.99', 19.99), ('d', '3.14159265358979323846', '3.14159265358979323846'), ('d', '1e999999999', '1e999999999'), ('d', '1e99999999999999999999', Written('1e99999999999999999999')),
            ('b', '340282366920938463463374607431768211456', 2**128), ('b', '-340282366920938463463374607431768211456', -2**128), ('i', '18446744073709551615', 2**64 - 1),
            ('i', '-9223372036854775808', -2**63), ('bu', '-1', '-1'), ('u', '"1e999"', '1e999'), ('u', '1.5', 1.5), ('u', '3.14159265358979323846', 3.141592653589793),
            ('w', '3', 3), ('w', '3.5', 3.5), ('c', '100', 100), ('q', '3.4e38', 3.4e38), ('v', '18446744073709551615', 2**64 - 1)]
    for k, v, w in nums:
        try: got = typed(N + f'--- !{k}\n{v}\n')[0]; f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', k, v, got)
        except REFUSED as e: f += 1; print('REFUSED', k, v, e)
    nope = [('i', '340282366920938463463374607431768211456'), ('i', '18446744073709551616'), ('i', '-9223372036854775809'), ('w', '18446744073709551616'), ('b', '"1"'), ('b', '1.0'),
            ('f', '1e999'), ('f', '-1e999'), ('f', '1.8e308'), ('f', str(TOP)), ('f', '"0.1"'), ('u', '1e999'), ('u', '-1.8e308'), ('d', '"19.99"'), ('c', '100.01'), ('q', '3.5e38'),
            ('v', '18446744073709551616'), ('v', '-1')]
    for k, v in nope:
        try: typed(N + f'--- !{k}\n{v}\n'); f += 1; print('NOT REFUSED', k, v)
        except REFUSED: pass
    bounds = [('!float(..0.1)', '0.1', 0.1), ('!float(0.1..)', '0.1', 0.1), ('!float(0.1..0.1)', '0.1', 0.1), ('!float(0.3..)', '0.3', 0.3), ('!float(..1.1)', '1.1', 1.1), ('!float(..0.1) | !str', '0.1', 0.1), ('!float(0.3..) | !str', '0.3', 0.3), ('!float(..0.1) | !str', '0.10000000000000001', '0.10000000000000001')]
    for tp, v, w in bounds:
        try: got = typed(f'--- &\nn: {tp}\n--- !n\n{v}\n')[0]; f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', tp, v, got)
        except REFUSED as e: f += 1; print('REFUSED', tp, v, e)
    outside = [('!float(..0.1)', '0.10000000000000001'), ('!float(0.1..)', '0.099999999999999999'), ('!float(..0.1)', '0.100000000000000000001')]
    for tp, v in outside:
        try: typed(f'--- &\nn: {tp}\n--- !n\n{v}\n'); f += 1; print('NOT REFUSED', tp, v)
        except REFUSED: pass
    # Section 4.4: float() rounds as exact arithmetic does, so every parser gets the same binary64 value.
    hard = ['0.1', '1.1', '3.14159265358979323846', '9007199254740993', '9007199254740995', '1.00000000000000011102230246251565404236316680908203125',
            '1.000000000000000111022302462515654042363166809082031250000001', '2.2250738585072011e-308', '2.4703282292062327e-324', '2.4703282292062328e-324',
            '4.9406564584124654e-324', '1e23', '8.589973e9', str(TOP - 1), '0.' + '9' * 800, '1' + '0' * 400 + 'e-400', '7.' + '0' * 1000 + '1e-1', '-0.' + '0' * 330 + '1']
    for v in hard:
        want = nearest(Decimal(v))
        try: got = typed(f'--- &\nn: !float\n--- !n\n{v}\n')[0]
        except REFUSED as e: f += 1; print('REFUSED', v[:40], e); continue
        if want is None or Fraction(got) != want: f += 1; print('NOT NEAREST', v[:40], got)
    floats = [('!float(0..1) | !str', '1e999', '1e999'), ('!float(..1) | !str', '3.14159265358979323846', '3.14159265358979323846'), ('!float(0..1) | !str', '1.5', '1.5'),
              ('!float', '0e99999999999999999999', 0.0), ('!float | !str', '-0.0e-99999999999999999999', -0.0), ('!float', '1e-99999999999999999999', 0.0),
              ('!float | !str', '1e-99999999999999999999', 0.0), ('!float(0..1)', '1e-99999999999999999999', 0.0), ('!float(..0) | !str', '1e-99999999999999999999', '1e-99999999999999999999'),
              ('!float(0..4)', '3.14159265358979323846', 3.141592653589793), ('!float(/[0-9.]+/)', '3.14159265358979323846', 3.141592653589793), ('!float', '1e39', 1e39),
              ('!float', '1.7e308', 1.7e308), ('!float', '4.9e-324', 5e-324), ('!float | !str', 'n/a', 'n/a'), ('!float(..1e99999999999999999999)', '1e308', 1e308),
              ('float: !int\nn: !float', '16777217', 16777217)]
    for tp, v, w in floats:
        body = tp if '\n' in tp else f'n: {tp}'
        try: got = typed(f'--- &\n{body}\n--- !n\n{v}\n')[0]; f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', tp, v, got)
        except REFUSED as e: f += 1; print('REFUSED', tp, v, e)
    floatnot = [('!float', '1e999'), ('!float', '1.8e308'), ('!float', '-1e400'), ('!float', str(TOP)), ('!float | !str', '1e999'), ('!float(0..) | !str', '1e999'),
                ('!float | !str', '1e99999999999999999999'), ('!float | !str', '0.4e0066999999999999999999999999999999'), ('!float(/[0-9e]+/) | !str', '1e99999999999999999999'),
                ('!float(/[0-9]+/) | !str', '9' * 400), ('!float', '"0.1"'), ('!float', 'abc'), ('!float(0..1)', '1.5'), ('!float(..0)', '1e-99999999999999999999')]
    for tp, v in floatnot:
        try: typed(f'--- &\nn: {tp}\n--- !n\n{v}\n'); f += 1; print('NOT REFUSED', tp, v)
        except REFUSED: pass
    # The width names and round on a float are gone (the user, 2026-11-12).
    gone = ['a: !float16', 'a: !bfloat16', 'a: !float32', 'a: !float64', 'a: !float128', 'a: !float(round)', 'a: !float(round 0..1)', 'a: !float(round /[0-9.]+/)',
            'a: !float(round 0..1 /[0-9.]+/)', 'a: {b: !float32(round)}']
    for g2 in gone:
        try: typed('--- &\n' + g2 + '\n'); f += 1; print('SCHEMA NOT REFUSED', g2)
        except REFUSED: pass
    decs = [(r'!decimal(/[-+]?[0-9]+\.[0-9]{2}/)', '+19.99', Decimal('19.99')), (r'!decimal(/\.[0-9]+/)', '.5', Decimal('0.5')), (r'!decimal(/[0-9]+\./)', '5.', Decimal('5')), (r'!decimal(/[0-9]{1,28}(\.[0-9]{1,10})?/)', '1234567890123456789012345678.1234567890', Decimal('1234567890123456789012345678.1234567890')), (r'!decimal(/0[0-9]+/)', '007', Decimal('7')), (r'!decimal(/[0-9]+e[0-9]+/)', '1e999999999', Decimal('1e999999999')), (r'!decimal(/[0-9]+\.[0-9]{2}/) | !str', '19.9', '19.9')]
    for tp, v, w in decs:
        try: got = typed(f'--- &\nn: {tp}\n--- !n\n{v}\n')[0]; f += 0 if got == w else 1; got == w or print('DIFFERS', tp, v, got)
        except REFUSED as e: f += 1; print('REFUSED', tp, v, e)
    decnot = [(r'!decimal(/[0-9]+\.[0-9]{2}/)', '19.9'), (r'!decimal(/[0-9]+\.[0-9]{2}/)', '"19.99"'), (r'!decimal(/[0-9]+\.[0-9]{2}/)', '19.999'), ('!decimal(/[a-z]+/)', 'abc'), ('!decimal(/[a-z]+/) | !str', 'abc'), ('!decimal(/[-+]/)', '+'), (r'!decimal(/\./)', '.'), ('!decimal(/[0-9]+/)', '1.5'), ('!decimal(/[0-9]+e/)', '1e')]
    for tp, v in decnot:
        try: typed(f'--- &\nn: {tp}\n--- !n\n{v}\n'); f += 1; print('NOT REFUSED', tp, v)
        except REFUSED: pass
    # Section 4.5 on !float, !decimal and !null; 4.6, precision and scale; 4.7, all three together.
    F = r'/[-+]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][-+]?[0-9]+)?/'
    more = [(f'!float({F})', '.5', 0.5), (f'!float({F})', '1.', 1.0), (f'!float({F})', '+1.5e3', 1500.0), (f'!float({F})', '007', 7.0), (f'!float({F})', '-0', 0.0),
            ('!float(/[0-9]+/) | !str', 'abc', 'abc'), ('!float(/[0-9]+/) | !str', '1.5', '1.5'), (f'!float({F}) | !str', '"5"', '5'),
            ('!null(/(~|null)?/)', '~', None), ('!null(/(~|null)?/)', 'null', None), ('!null(/(~|null)?/)', '', None), ('!null(/~/) | !str', 'null', 'null'),
            ('!null(/~/) | !str', '"~"', '~'), ('a:\n  !**: !null(/~/) | !int\nn: !a', 'x: ~\ny: [1, ~]', {'x': None, 'y': [1, None]}),
            ('!decimal(5:2)', '999.99', Decimal('999.99')), ('!decimal(5:2)', '-999.99', Decimal('-999.99')), ('!decimal(5:2)', '1.50', Decimal('1.50')),
            ('!decimal(5:2)', '0.0', Decimal('0.0')), ('!decimal(5:2)', '1e2', Decimal('1e2')), ('!decimal(5:2)', '100e-2', Decimal('1.00')), ('!decimal(5:4)', '0.0012', Decimal('0.0012')),
            ('!decimal(5:0)', '99999', Decimal('99999')), ('!decimal(5:0)', '1.0', Decimal('1.0')), ('!decimal(5:5)', '0.12345', Decimal('0.12345')),
            ('!decimal(38:10)', '1234567890123456789012345678.1234567890', Decimal('1234567890123456789012345678.1234567890')), ('!decimal(1:0)', '0e999999999', Decimal('0')),
            ('!decimal(5:2) | !str', '1.005', '1.005'), ('[!decimal(5:2), ...]', '[1.5, 2]', [Decimal('1.5'), Decimal('2')]), ('{a: !decimal(5:2)}', '{a: 1.5}', {'a': Decimal('1.5')}),
            ('!int(0..100 /[-+][0-9]+/)', '+5', 5), ('!int(0..100 /[-+][0-9]+/)', '-0', 0), ('!int(..10 /0[0-9]+/)', '007', 7), ('!str(1..8 /[a-z]+/)', 'web', 'web'),
            ('!decimal(38:10 0..)', '19.99', Decimal('19.99')), (r'!decimal(5:2 0.. /[0-9]+\.[0-9]{2}/)', '19.99', Decimal('19.99')), (r'!decimal(5:2 /[0-9]+\.[0-9]{2}/)', '19.99', Decimal('19.99')),
            (r'!float(0..1 /[0-9]*\.[0-9]+/)', '.5', 0.5), (r'!float(0..1 /[0-9]*\.[0-9]+/)', '.1', 0.1), ('!int(1..10) | !int(20..30)', '25', 25), ('!int(1..10) | !int(20..30) | !str', '15', '15'),
            ('!decimal(5:2 0..) | !str', '-1', '-1'), ('!decimal', '0e99999999999999999999', Written('0e99999999999999999999')), ('!decimal(0..1)', '-0e-99999999999999999999', Written('-0e-99999999999999999999')),
            ('!decimal | !str', '1e99999999999999999999', Written('1e99999999999999999999')), ('!decimal(5:2) | !str', '1e99999999999999999999', '1e99999999999999999999'),
            ('!decimal(/[0-9e]+/) | !str', '1e99999999999999999999', Written('1e99999999999999999999')), ('!decimal(0..) | !str', '-1e99999999999999999999', '-1e99999999999999999999'),
            ('!decimal(/[0-9e]+/)', '007e5', Decimal('7e5')), ('!float(/[0-9.]+/) | !str', '3.14159265358979323846', 3.141592653589793)]
    for tp, v, w in more:
        try: got = typed(f'--- &\nn: {tp}\n--- !n\n{v}\n'.replace('n: a:\n', 'a:\n'))[0]; f += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', tp, v, got)
        except REFUSED as e: f += 1; print('REFUSED', tp, v, e)
    morenot = [('!float(/[a-z]+/)', 'abc'), ('!float(/[a-z]+/) | !str', 'abc'), ('!float(/[0-9]+/)', '1.5'), ('!float(/[-+0-9.]+/) | !str', '1.2.3'), ('!decimal(/[a-z]+/) | !str', 'inf'), ('!decimal(/[0-9_]+/) | !str', '1_000'), ('!decimal(/[٠-٩]+/) | !str', '١٢٣'), ('!float(/[0-9]+/) | !str', '9' * 400),
               (f'!float({F})', '"5"'), ('!decimal(5:2)', '1e99999999999999999999'),
               ('!null(/~/)', 'null'), ('!null(/~/)', '"~"'), ('!null(/(~|null)?/)', 'x'), ('!null(/~/)', '[~]'), ('!null(/~/)', "'~'"),
               ('!decimal(5:2)', '1000'), ('!decimal(5:2)', '1.005'), ('!decimal(5:2)', '-1000'), ('!decimal(5:2)', '1e3'), ('!decimal(5:2)', '1e-3'), ('!decimal(5:2)', '1e999999999'),
               ('!decimal(5:2)', '1e-999999999'), ('!decimal(5:5)', '1'), ('!decimal(5:2)', '"1.5"'), ('!decimal(38:10)', '12345678901234567890123456789'), ('!decimal(38:10)', '0.12345678901'),
               ('!int(0..100 /[-+][0-9]+/)', '+101'), ('!int(0..100 /[-+][0-9]+/)', '5'), ('!int(0..100 /[-+][0-9]+/)', '-1'), ('!int(..10 /0[0-9]+/)', '011'),
               ('!str(1..8 /[a-z]+/)', 'abcdefghi'), ('!str(1..8 /[a-z]*/)', "''"), ('!decimal(38:10 0..)', '-1'), (r'!decimal(5:2 0.. /[0-9]+\.[0-9]{2}/)', '19.9'),
               (r'!decimal(5:2 0.. /[0-9]+\.[0-9]{2}/)', '1000.00'), ('!int(1..10) | !int(20..30)', '15'), ('!decimal(5:2 /[a-z]+/) | !str', 'abc')]
    for tp, v in morenot:
        try: typed(f'--- &\nn: {tp}\n--- !n\n{v}\n'); f += 1; print('NOT REFUSED', tp, v)
        except REFUSED: pass
    fulls = [('a: !str\n', 'a', 1), ('a: !int | x\n', 'a', 2), ('big: !int | !str\na: !big | x\n', 'a', 6), ('m:\n  x: !int\n  y?: !str\nu: !m | !int\n', 'u', 10), ('a: !str(/ab{3}/)\n', 'a', 4), ('a: !b | !b\nb: !int\n', 'a', 5), ('a: [!int, ...]\n', 'a', 2), ('a:\n  !**:\n    n: !int\n    !str(/x/): !int\n    !*: !str\n', 'a', 9), ('a:\n  n: !int\n  !*: !str\n', 'a', 5), ('a:\n  !**: !int\n', 'a', 3), ('a: !b\nb: !c\nc: !str\n', 'a', 6)]
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
    # Section 3: part 1's limit applies to an application's schema. `a: !str` holds 7 as text, and its full size is 1.
    try: typed('%YAML 2.0\n', ('--- &\na: !str\n', 'a'), limit=7)
    except REFUSED as e: f += 1; print('REFUSED: an application schema at its held size', e)
    try: typed('%YAML 2.0\n', ('--- &\na: !str\n', 'a'), limit=6); f += 1; print("NOT REFUSED: an application schema past part 1's limit")
    except No: pass
    emptyseq = ['[""]', '[a]', 'abc', '{}']
    for v in emptyseq:
        try: typed(f'%YAML 2.0\n--- &\nu: !int | []\n--- !u\n{v}\n'); f += 1; print('NOT REFUSED', v)
        except REFUSED: pass
    # The third review (2026-11-11): each point as the text now says it.
    third = 0
    T3 = '--- &\nbase: {why?: !int}\nt:\n  <<: *base\n  "why?": !str\n  !*: !int\n'
    T3b = '--- &\nbase: {"why?": !int}\nt:\n  <<: *base\n  why?: !str\n  !*: !int\n'
    C3 = '--- &\ncircle:\n  kind: circle | !int\n  r: !int\nsquare:\n  kind: square\n  r: !int\nshape: !circle | !square\n'
    alts = '|'.join(chr(0x4E00 + i) for i in range(1100))
    def maps3(w): return f'm1:\n  !str(/a{{{w}}}/): !str\nm2:\n  !str(/b{{{w}}}/): !str\nu: !m1 | !m2\n'
    goods3 = [('--- &\nn: !any | !int\n--- !n\n3\n', 3), ('--- &\nn: !any | !int\n--- !n\nabc\n', 'abc'), ('--- &\nn: !any | x\n--- !n\nx\n', 'x'),
              (T3 + '--- !t\nwhy?: 5\n', {'why?': '5'}), (T3b + '--- !t\nwhy?: 5\n', {'why?': 5}), (T3b + '--- !t\n{}\n', {}),
              ('--- &\nt:\n  a: !int\n  a?: !str\n--- !t\n{}\n', {}), ('--- &\nn: !binary\n--- !n\naGk=\n', 'aGk='), ('--- &\nn: !binary\n--- !n\n""\n', ''),
              ('--- &\nn: !float | !str\n--- !n\n1E5\n', 100000.0), ('--- &\nn: !float\n--- !n\n1e+5\n', 100000.0), ('--- &\nn: !float\n--- !n\n1.79769313486231570815e308\n', 1.7976931348623157e308),
              ('--- &\nn: !decimal(5:2)\n--- !n\n1.500\n', Decimal('1.500')), ('--- &\nn: !int(0..10) | !str\n--- !n\n11\n', '11'), ('--- &\nn: !int(0..10) | !str\n--- !n\n1' + '0' * 29 + '\n', '1' + '0' * 29), ('--- &\nn: !bigint(/[-+][0-9]+/)\n--- !n\n+0012\n', 12), ('--- &\nn: !bigint(0..10) | !str\n--- !n\n1' + '0' * 29 + '\n', '1' + '0' * 29),
              ('--- &\nm:\n  !str(/a.b/): !int\n  !*: !str\n--- !m\n"a\\rb": 1\n', {'a\rb': '1'}), ('--- &\nm:\n  !str(/a.b/): !int\n  !*: !str\n--- !m\naxb: 1\n', {'axb': 1}),
              ('--- &\nn: !str(/\\p{Lu}[a-z]*/) | !int\n--- !n\nAbc\n', 'Abc'), ('--- &\nn: !str(/[\\p{L}\\p{Nd}]+/)\n--- !n\nÀ1\n', 'À1'), ('--- &\nn: !str(/\\P{L}+/) | !str\n--- !n\n12\n', '12'),
              ('--- &\nn: !str(/[-a]+/)\n--- !n\na-a\n', 'a-a'), ('--- &\nn: !str(/[a-]+/)\n--- !n\n-a\n', '-a'), ('--- &\nn: !str(/\\.\\{\\}/)\n--- !n\n".{}"\n', '.{}'),
              ('--- &\nn: !str(1..5 /[)]+/) | !int\n--- !n\n")))"\n', ')))'), ('--- &\nn: a(/b | !int\n--- !n\na(/b\n', 'a(/b'), ('--- &\nn: f(x) | !int\n--- !n\nf(x)\n', 'f(x)'),
              (C3.replace('circle | !int', 'circle') + '--- !shape\n{kind: square, r: 1}\n', {'kind': 'square', 'r': 1}),
              ('--- &\nm:\n  !float: !int\n  !*: !str\n--- !m\n3.14159265358979323846: 5\n', {'3.14159265358979323846': 5})]
    for s3, w in goods3:
        try: got = typed(s3)[0]; third += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', repr(s3), got)
        except REFUSED as e: third += 1; print('REFUSED', repr(s3), e)
    bads3 = ['--- &\nn: !int(0..) | !str\n--- !n\n1' + '0' * 29 + '\n', '--- &\nn: !int | !str\n--- !n\n1' + '0' * 29 + '\n', T3 + '--- !t\n{}\n', '--- &\nn: !binary | !int\n--- !n\naGl=\n', '--- &\nn: !binary\n--- !n\naGk\n', '--- &\nn: !binary\n--- !n\n"aGVs\\r\\nbG8="\n',
             '--- &\nn: !float | !str\n--- !n\n1.8e308\n', '--- &\nm:\n  !float: !int\n  !*: !str\n--- !m\n1e999: 5\n', C3 + '--- !shape\n{kind: square, r: 1}\n',
             '--- &\nn: !str(/\\p{Lu}/)\n--- !n\na\n']
    for s3 in bads3:
        try: typed(s3); third += 1; print('NOT REFUSED', repr(s3))
        except REFUSED: pass
    schemas3 = ['a: !bigint(round)', 'a: !bigint(..)', 'a: !int(1:0)', 'a: !int(..)', 'a: !int |  x', 'a: x  | !int', 'a: !str(/a{,3}/)', 'a: !str(/a{/)', 'a: !str(/a}/)', 'a: !str(/\\x41/)', 'a: !str(/\\u0041/)', 'a: !str(/a**/)',
                'a: !str(/a{2}{3}/)', 'a: !str(/[a[b]/)', 'a: !str(/[]/)', 'a: !str(/[a-b-c]/)', 'a: !str(/a{3,2}/)', 'a: !str(/\\p{Xx}/)', 'a: !str(/\\p{Cs}/)', 'a: !str(/(?:a)/)',
                'a: !str(/a)/)', 'a: !str(/(a/)', f'a: !str(/{alts}/)', 'a: !str(/x{1025,}/)', 'a: !str(/(a|b){513}/)', maps3(600), 'a: !str(/' + '(' * 257 + 'a' + ')' * 257 + '/)']
    for s3 in schemas3:
        try: typed('--- &\n' + s3 + '\n'); third += 1; print('SCHEMA NOT REFUSED', s3)
        except REFUSED: pass
    loads3 = ['a: !str(/x{1024,}/)', 'a: !str(/(a|b){512}/)', 'a: !str(/a{0}b/)', 'a: !str(/(|a)/)', maps3(500), 'a: !str(/' + '(' * 256 + 'a' + ')' * 256 + '/)']
    for s3 in loads3:
        try: typed('--- &\n' + s3 + '\n')
        except REFUSED as e: third += 1; print('SCHEMA REFUSED', s3, e)
    for pt, n3 in [('abc|abd', 6), ('a|b|c', 3), ('(a{1000}){1000}', 10 ** 6), ('[a-z]+x?', 2), ('\\p{L}.', 2), ('x{3,}', 3), ('x{0,}y*', 2)]:
        if pattern(pt, pt)[1].count != n3: third += 1; print('COUNT', pt, pattern(pt, pt)[1].count, n3)
    for z3 in ('-0', '-1e-400', '-1e-99999999999999999999'):
        s3 = f'--- &\nn: !float\n--- !n\n{z3}\n'
        try: z = typed(s3)[0]
        except REFUSED as e: third += 1; print('REFUSED', repr(s3), e); continue
        if not (z == 0 and str(z) == '-0.0'): third += 1; print('SIGN OF ZERO', repr(s3), z)
    def pub3(body):
        b = ('%YAML 2.0\n' + body).encode(); h = hashlib.sha256(b).hexdigest()
        return typed(f'--- !x.org/b.yes#sha256={h}\ntrue\n', store={h: b})[0]
    if pub3('--- &\na: !int\nb: !bool\n') is not True: third += 1; print('PUBLISHED ROOT')
    for body3 in ('--- &\na: !int\nb: !str\n--- &\na: !bool\n', '--- &\na: !int\nb: !bool\n...\n', '--- &\na: !int\nb: !bool\n---\nx\n'):
        try: pub3(body3); third += 1; print('PUBLISHED NOT REFUSED', repr(body3))
        except REFUSED: pass
    third_n = len(goods3) + len(bads3) + len(schemas3) + len(loads3) + 7 + 3 + 1 + 3
    f += third
    # Section 11's typed count (2026-11-12), as an interface that keeps references counts it. Each stream
    # passes at its limit and is refused at one less; without keep, typed has no limit.
    tyd = 0
    S11 = '--- &\ns: abcdefgh\none: [!str, ...]\nthree: [!str(/a.*/), !str(/.*h/), !str(1..)]\n'
    X11 = '--- &\nx: {n: abcdefgh}\njob: {n: !str}\n'
    STAR = '--- &\nv: {x: 1}\nleaf: {}\nroot:\n  a:\n    child: !leaf\n    !**: !int\n  b:\n    child: !leaf\n    !**: !str\n--- !root\na:\n  child: *v\nb:\n  child: *v\n'
    counts = [(S11 + '--- !one\n[*s, *s, *s]\n', 10), (S11 + '--- !three\n[*s, *s, *s]\n', 28),
              (X11 + 'pair: {a: !job, b: !job}\n--- !pair\n{a: *x, b: *x}\n', 17),  # a name is its entry's type
              (X11 + 'pair: {a: {n: !str}, b: {n: !str}}\n--- !pair\n{a: *x, b: *x}\n', 29),  # two places, two types
              (X11 + 'pair: {a: !job, b: !job}\n--- !pair\n{a: {n: abcdefgh}, b: {n: abcdefgh}}\n', 29),  # no references
              (STAR, 29),  # the same node under two nearest `!**`
              # A collection reached only through `!**`: the root 5, `v` once 3, its `1` 2.
              ('--- &\nv: {x: 1}\nroot:\n  !**: !int\n--- !root\na: *v\nb: *v\n', 10),
              # Keys tried against a type key count with their mapping, not again: 5, `v` 4, its `1` 2.
              ('--- &\nv: {k1: 1}\nroot:\n  !**:\n    !str(/k.*/): !int\n--- !root\na: *v\nb: *v\n', 11)]
    for st, n in counts:
        try: typed(st, keep=True, limit=n)
        except REFUSED as e: tyd += 1; print('TYPED REFUSED AT', n, repr(st[-40:]), e)
        try: typed(st, keep=True, limit=n - 1); tyd += 1; print('TYPED NOT REFUSED AT', n - 1, repr(st[-40:]))
        except REFUSED: pass
        try: typed(st, limit=n - 1)
        except REFUSED as e: tyd += 1; print('REFUSED WITHOUT KEEP AT', n - 1, repr(st[-40:]), e)
    big = 'a' * 2 ** 20; refs = '[' + ', '.join(['*s'] * 1000) + ']\n'
    many = '--- &\ns: ' + big + '\nrow: [' + ', '.join(f'!str({k}..)' for k in range(1, 1001)) + ']\n--- !row\n' + refs
    same1 = '--- &\ns: ' + big + '\nrow: [!str, ...]\n--- !row\n' + refs
    try: typed(many, keep=True); tyd += 1; print('1,000 TYPES OF 1 MB NOT REFUSED')
    except REFUSED: pass
    for st, kw in ((many, {}), (same1, {'keep': True})):
        try: typed(st, **kw)
        except REFUSED as e: tyd += 1; print('TYPED REFUSED', kw, e)
    # An application's schema serves both documents, and typed counts each one on its own: 18 each, so
    # 18 allows both. The schema's text holds 14 under part 1's limit (section 3), so typed binds first.
    app2 = ('--- &\none: [!str, ...]\n', 'one'); two = '--- &\ns: abcdefghabcdefgh\n---\n[*s, *s, *s]\n---\n[*s, *s, *s]\n'
    try: typed(two, app=app2, keep=True, limit=18)
    except REFUSED as e: tyd += 1; print('TYPED COUNTS ACROSS DOCUMENTS', e)
    try: typed(two, app=app2, keep=True, limit=17); tyd += 1; print('TYPED NOT REFUSED AT 17, APP')
    except REFUSED as e:
        if 'typed passes' not in str(e): tyd += 1; print('NOT REFUSED BY TYPED AT 17, APP', e)
    typed_n = 3 * len(counts) + 3 + 2
    f += tyd
    # Dates (the user, 2026-11-11 and 2026-11-12): RFC 3339's grammar, a date a parser can't hold refusing
    # the document, and an application's cut, which keeps the digits a parser holds and refuses the rest.
    prec = 0
    def one(tp, v, **kw): return typed(f'--- &\nn: {tp}\n--- !n\n{v}\n', **kw)[0]
    T = '2001-02-03T04:05:06'
    goodsP = [('!datetime', T + 'Z', T + 'Z', {}), ('!datetime', '2001-02-03t04:05:06z', '2001-02-03t04:05:06z', {}),
              ('!datetime', '1990-12-31T23:59:60Z', '1990-12-31T23:59:60Z', {}), ('!datetime', '1990-12-31T18:59:60-05:00', '1990-12-31T18:59:60-05:00', {}),
              ('!datetime', '1991-01-01T00:59:60+01:00', '1991-01-01T00:59:60+01:00', {}), ('!datetime', '2016-12-31T23:59:60.5Z', '2016-12-31T23:59:60.5Z', {}),
              ('!datetime', T + '-00:00', T + '-00:00', {}), ('!datetime', T + '+23:59', T + '+23:59', {}), ('!date', '2000-02-29', '2000-02-29', {}),
              ('!date', '0000-02-29', '0000-02-29', {}), ('!date', '0000-01-01', '0000-01-01', {}),
              ('!datetime | !str', '2001-02-03 04:05:06Z', '2001-02-03 04:05:06Z', {}), ('!date | !str', '2001-02-29', '2001-02-29', {}),
              ('!date | !str', '1900-02-29', '1900-02-29', {}), ('!datetime | !str', '1990-12-30T23:59:60Z', '1990-12-30T23:59:60Z', {}),
              ('!datetime | !str', '1990-12-31T23:58:60Z', '1990-12-31T23:58:60Z', {}), ('!datetime | !str', '1990-12-31T23:59:60+01:00', '1990-12-31T23:59:60+01:00', {}),
              ('!datetime | !str', '2001-02-03T24:00:00Z', '2001-02-03T24:00:00Z', {}), ('!datetime | !str', T + '+24:00', T + '+24:00', {}),
              ('!datetime | !str', T + '.Z', T + '.Z', {}), ('!datetime | !str', T, T, {}), ('!datetime', T + '.123456789012Z', T + '.123456789012Z', {}),
              ('!datetime', T + '.1234567Z', T + '.1234567Z', {'cut': True}), ('[!datetime, ...]', f'[{T}.5Z]', [T + '.5Z'], {})]
    for tp, v, w, kw in goodsP:
        try: got = one(tp, v, **kw); prec += 0 if same(got, w) else 1; same(got, w) or print('DIFFERS', tp, v, kw, got)
        except REFUSED as e: prec += 1; print('REFUSED', tp, v, kw, e)
    badsP = [('!datetime', '2001-02-03 04:05:06Z', {}), ('!date', '1900-02-29', {}), ('!datetime', '1990-12-30T23:59:60Z', {}), ('!date', '2001-00-10', {}),
             ('!datetime', '1990-12-31T23:58:60Z', {}), ('!datetime', '1990-12-31T23:59:60+01:00', {}), ('!datetime', '2001-02-03T24:00:00Z', {}),
             ('!datetime', T + '+24:00', {}), ('!datetime', T + '.Z', {}), ('!datetime', T, {}), ('!date', '2001-02-29', {}), ('!datetime', '1991-01-01T00:59:60+00:30', {}),
             ('!datetime', '2001-02-03 04:05:06Z', {'cut': True})]
    for tp, v, kw in badsP:
        try: one(tp, v, **kw); prec += 1; print('NOT REFUSED', tp, v, kw)
        except REFUSED: pass
    # A parser that holds what Python's datetime does, then JavaScript's Date, then one that holds no fraction.
    C = {'cut': True}
    holds = [((6, False, False), [('!datetime', T + '.123456Z', T + '.123456Z', {}), ('!datetime | !str', T + 'x', T + 'x', {}), ('!datetime', T + '.1234567Z', T + '.123456Z', C),
                                  ('!datetime', '1999-12-31T23:59:59.9999999Z', '1999-12-31T23:59:59.999999Z', C), ('!datetime | !str', T + '.1234567+05:30', T + '.123456+05:30', C),
                                  ('!datetime', T + '.12Z', T + '.12Z', C)],
              [('!datetime | !str', T + '.1234567Z', {}), ('!datetime', T + '.1234567Z', {}), ('!datetime | !str', '1990-12-31T23:59:60Z', {}), ('!date | !str', '0000-01-01', {}),
               ('!datetime', '1990-12-31T23:59:60Z', C), ('!date', '0000-01-01', C), ('!datetime', '0000-01-01T00:00:00.1234567Z', C)]),
             ((3, False, True), [('!date', '0000-01-01', '0000-01-01', {}), ('!datetime', T + '.98765Z', T + '.987Z', C), ('!datetime', T + '.123Z', T + '.123Z', {})],
              [('!datetime', T + '.1234Z', {}), ('!datetime | !str', '2016-12-31T23:59:60Z', {}), ('!datetime', '2016-12-31T23:59:60.12345Z', C)]),
             ((0, True, True), [('!datetime', T + '.9Z', T + 'Z', C), ('!datetime', '2016-12-31T23:59:60.5Z', '2016-12-31T23:59:60Z', C), ('!datetime', T + 'Z', T + 'Z', {})],
              [('!datetime', T + '.9Z', {}), ('!datetime | !str', T + '.0Z', {})])]
    nholds = 0
    for hold, oks, nos in holds:
        DATEHOLD = hold
        for tp, v, w, kw in oks:
            nholds += 1
            try: got = one(tp, v, **kw); prec += 0 if got == w else 1; got == w or print('DIFFERS', hold, tp, v, kw, got)
            except REFUSED as e: prec += 1; print('REFUSED', hold, tp, v, kw, e)
        for tp, v, kw in nos:
            nholds += 1
            try: one(tp, v, **kw); prec += 1; print('NOT REFUSED', hold, tp, v, kw)
            except REFUSED: pass
    DATEHOLD = None
    # Levels and round on dates are gone (the user, 2026-11-12), and round was already gone on floats.
    schemasP = ['a: !datetime(3)', 'a: !datetime(0)', 'a: !datetime(round 3)', 'a: !datetime(round 9)', 'a: [!datetime(round 3), ...]', 'a: !datetime(round 3) | !str',
                'a: !datetime(round)', 'a: !date(3)', 'a: !date(round)', 'a: !int(round)', 'a: !decimal(round 5:2)', 'a: !str(round)', 'a: !null(round)',
                'a: !bool(round)', 'a: !datetime(3 3)', 'a: !datetime(03)', 'a: !datetime(0..1)', 'a: !datetime(3 0..1)', 'a: !float(round round)',
                'a: !float(round  0..1)', 'a: !float( round)', 'a: !float(0..1 round)', 'a: !datetime(-1)', 'a: !datetime(round 3 /x/)',
                'a: !int(3)', 'a: !float(round 3)', 'a: !datetime(round3)', 'a: {b: !datetime(6)}']
    for sP in schemasP:
        try: typed('--- &\n' + sP + '\n'); prec += 1; print('SCHEMA NOT REFUSED', sP)
        except REFUSED: pass
    loadsP = ['a: !datetime', 'a: [!datetime, ...]', 'a: !datetime | !str', 'a: !float(0..1 /[0-9.]+/)', 'a: !decimal(5:2 0..1 /[0-9.]+/)']
    for sP in loadsP:
        try: typed('--- &\n' + sP + '\n')
        except REFUSED as e: prec += 1; print('SCHEMA REFUSED', sP, e)
    prec_n = len(goodsP) + len(badsP) + nholds + len(schemasP) + len(loadsP)
    f += prec; third_n += prec_n
    print(f'edge cases: {len(hard) + len(floats) + len(floatnot) + len(gone) + len(decs) + len(decnot) + len(more) + len(morenot) + len(bounds) + len(outside) + len(good) + len(emptyseq) + 2 * len(fulls) + 7 + len(no) + len(schemas) + len(ints) + len(notints) + 1 + len(forms) + 1 + len(says) + 2 + len(unions) + len(star) + len(notstar) + len(badstar) + len(pub) + len(notpub) + 1 + 1 + len(reach) + len(nums) + len(nope) + third_n + typed_n} run, {f} fail')
    sys.exit(1 if bad or f else 0)
