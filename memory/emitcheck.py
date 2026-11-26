"""Write every typed test of part 2's suite out again, as section 13 says, and read it back.

    python3 -I emitcheck.py SUITE [--mark] [-v]     (SUITE is the code checkout's suite/ directory)

Checks that each test is marked `emit: refused` exactly where its typed events can't be written. With
--mark it marks them instead, as suiteyes.py has it do after writing the suite. -v shows every
document not written back, not only two of each kind.

A throwaway emitter written from part 2's section 13, not a reference. For each accepted test with
typed events, it types the stream with schemacheck.py, then writes each document from its typed
values alone, as an emitter given typed data would: a string plain where part 1 reads it back as
that text, else double-quoted; every other scalar in its standard spelling (a float as section 4.4
says). No text kept from the reading is used. It reads the result back with the same schema, and
quotes a string that came back as something else. What still comes back different is refused.

With `bind`, each bound name's value is the application's object, and it must come back through the
same name. A bound name's code gives back what it was given, unless the test has `writes`, which gives
what the code writes instead: a string, written as spelled, or a mapping. For those, only the name is
checked, since the code answers for the value (section 13).

Section 13 says an emitter never has to respell anything, since a scalar's spelling never changes the
type of anything above it. Quoting a string after reading back is this checker's shortcut for knowing
the type at its place, and it checks the claim: quoting one scalar must change no other.
"""
import base64, math, os, re, struct, sys
from collections import Counter
from decimal import Decimal
here = os.path.dirname(os.path.abspath(__file__))
whole = open(here + '/schemacheck.py', encoding='utf-8').read()
ns = {'__name__': 'sc', '__file__': here + '/schemacheck.py'}
exec(compile(whole.split("\nif __name__ == '__main__':")[0], here + '/schemacheck.py', 'exec'), ns)
REFUSED, LIMIT, No, Schema, typed, read = (ns[k] for k in 'REFUSED LIMIT No Schema typed read'.split())

class Tag:
    """A typed scalar the checker gives as a str, int or Decimal: its type, and its text."""
    def __init__(s, kind, text): s.kind, s.text = kind, text
    def __repr__(s): return f'!{s.kind} {s.text}'
scalar0 = Schema.scalar
def scalar(s, name, lim, v, path):
    out = scalar0(s, name, lim, v, path)
    if name in ('date', 'datetime', 'binary'): return Tag(name, out)
    if name == 'bigint': return Tag(name, str(out))
    if name == 'decimal': return Tag(name, ns['canon'](str(v)) if lim and lim[1] else str(v))
    return out
Schema.scalar = scalar

class Obj:
    """An application's object: what a bound name's code made (section 12), with the name and what it was given."""
    def __init__(s, name, v): s.name, s.v = name, v
    def __repr__(s): return f'{s.name}({s.v!r})'
def called(s, t, i, out):
    """As the checker's, and the value becomes the application's object."""
    if ns['BIND'] and not s.quiet:
        bound = [n for n in s.memo[id(t)][2][i] if n in ns['BIND']]
        if bound: ns['CALLS'].append(bound[0]); return Obj(bound[0], out)
    return out
Schema.called = called
class Spelled(str):
    """The text a bound name's code writes for a scalar, written as spelled (section 13)."""
WR = {}
def written(v):
    """What the emitter is given to write: each object through its code. A name the test gives `writes` for
    writes that, a string as spelled and a mapping as it is; any other bound name's code gives back what it
    was given, as the suite's bindings do."""
    if isinstance(v, Obj):
        if v.name not in WR: return written(v.v)
        w = WR[v.name]
        return Spelled(w) if isinstance(w, str) else w
    if isinstance(v, dict): return {k: written(x) for k, x in v.items()}
    if isinstance(v, list): return [written(x) for x in v]
    return v
def quotable(v):
    """A string the emitter may quote: not a time or the like, and not text bound code spelled."""
    return isinstance(v, str) and not isinstance(v, (Tag, Spelled))

def key(v):
    """v with its types, to compare: a float by its bits, so the sign of zero counts, and a time with
    T and Z in capitals, since lowercase is the same time (section 4.8)."""
    if isinstance(v, dict): return ('map', tuple((k, key(x)) for k, x in v.items()))
    if isinstance(v, list): return ('seq', tuple(key(x) for x in v))
    if isinstance(v, Tag): return (v.kind, v.text.upper() if v.kind == 'datetime' else v.text)
    if v is None: return ('null',)
    if isinstance(v, bool): return ('bool', v)
    if isinstance(v, int): return ('int', v)
    if isinstance(v, float): return ('float', struct.pack('>d', v))
    if isinstance(v, str): return ('str', v)
    raise TypeError(repr(v))

def floating(x):
    """Section 4.4: the fewest significant digits that read back; positional for zero and from 1e-7 up
    to 1e21, with .0 when there is no fraction; otherwise an exponent with its sign."""
    sign = '-' if math.copysign(1, x) < 0 else ''; x = abs(x)
    if x == 0: return sign + '0.0'
    d = Decimal(repr(x))  # repr gives the fewest digits that read back
    digits = ''.join(map(str, d.as_tuple().digits)).strip('0'); e10 = d.adjusted()
    if 1e-7 <= x < 1e21:
        if e10 >= 0: whole, frac = digits[:e10 + 1].ljust(e10 + 1, '0'), digits[e10 + 1:] or '0'
        else: whole, frac = '0', '0' * (-e10 - 1) + digits
        return f'{sign}{whole}.{frac}'
    return f'{sign}{digits[0]}{"." + digits[1:] if len(digits) > 1 else ""}e{"+" if e10 >= 0 else "-"}{abs(e10)}'

def spelling(v):
    """Every scalar but a string: its standard spelling."""
    if isinstance(v, Tag):
        # A date, a time, base64 and a decimal are delivered as their text (section 4). A time is
        # written with T and Z in capitals, as the engine does, and compared so (section 4.8).
        return v.text.upper() if v.kind == 'datetime' else v.text
    if v is None: return 'null'
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, int): return str(v)
    if isinstance(v, float): return floating(v)
    raise TypeError(repr(v))

PLAINSTART = set('-?:,[]{}#&*!|>\'"%@`<. \t')
def plain_ok(t):
    """Conservative: text part 1 surely reads back, plain, as itself. Anything else is quoted."""
    if not t or t[0] in PLAINSTART or t[-1] in ' \t:': return False
    if any(c in t for c in '\n\r\t,[]{}') or ': ' in t or ' #' in t: return False
    return all(0x20 <= ord(c) < 0x7f or (ord(c) >= 0xa0 and ord(c) not in (0x2028, 0x2029, 0xfeff, 0xfffe, 0xffff) and not 0xd800 <= ord(c) < 0xe000) for c in t)
def dq(t):
    out = []
    for c in t:
        o = ord(c)
        if c == '"': out.append('\\"')
        elif c == '\\': out.append('\\\\')
        elif c == '\n': out.append('\\n')
        elif c == '\t': out.append('\\t')
        elif c == '\r': out.append('\\r')
        elif o < 0x20 or 0x7f <= o < 0xa0 or o in (0x2028, 0x2029, 0xfeff, 0xfffe, 0xffff) or 0xd800 <= o < 0xe000: out.append(f'\\u{o:04x}')
        else: out.append(c)
    return '"' + ''.join(out) + '"'

def text(v, path, quote):
    if isinstance(v, Spelled): return str(v) if plain_ok(v) else dq(v)
    if isinstance(v, str) and not isinstance(v, Tag): return dq(v) if path in quote or not plain_ok(v) else v
    if v is None and path in quote: return ''
    return spelling(v)
def block(v, ind, path, quote):
    """Lines for v at indent ind; or one inline text, for a scalar or an empty collection."""
    pad = ' ' * ind
    if isinstance(v, dict) and v:
        lines = []
        for k, x in v.items():
            kt = dq(k) if path + (('key', k),) in quote or not plain_ok(k) else k
            b = block(x, ind + 2, path + (k,), quote)
            if b == '': lines.append(f'{pad}{kt}:')
            elif isinstance(b, str): lines.append(f'{pad}{kt}: {b}')
            else: lines.append(f'{pad}{kt}:'); lines += b
        return lines
    if isinstance(v, list) and v:
        lines = []
        for i, x in enumerate(v):
            b = block(x, ind + 2, path + (i,), quote)
            if b == '': lines.append(f'{pad}-')
            elif isinstance(b, str): lines.append(f'{pad}- {b}')
            else: lines.append(f'{pad}- {b[0][ind + 2:]}'); lines += b[1:]
        return lines
    if isinstance(v, dict): return '{}'
    if isinstance(v, list): return '[]'
    return text(v, path, quote)

MARK = re.compile(r'(---|\.\.\.)(?=[ \t\r\n]|$)')
def chunks(stream):
    """The stream cut at its marker lines, which are never inside a node (part 1, section 4.4)."""
    out = [['pre', '']]
    for line in stream.splitlines(keepends=True):
        m = MARK.match(line)
        if m and m[1] == '---': out.append(['table' if re.match(r'---[ \t]+&', line) else 'doc', line])
        elif m: out.append(['end', line])
        else: out[-1][1] += line
    return out

def emit_doc(name, v, quote):
    head = '---' + (f' !{name}' if name else '')
    b = block(v, 0, (), quote)
    return f'{head} {b}\n' if isinstance(b, str) else head + '\n' + '\n'.join(b) + '\n'

def diff(a, b, path, out):
    """Paths of scalars that differ; ('shape', path) where the trees themselves differ; ('name', path)
    where an object doesn't come back through its name."""
    if isinstance(a, Obj) or isinstance(b, Obj):
        if not (isinstance(a, Obj) and isinstance(b, Obj) and a.name == b.name): out.append(('name', path))
        if isinstance(a, Obj) and a.name in WR: return  # Section 13: the code answers for the value, so only the name is checked.
        # Code that gives back what it was given: compare the values too, so a string can still be quoted.
        a, b = (x.v if isinstance(x, Obj) else x for x in (a, b))
    if isinstance(a, dict):
        if not isinstance(b, dict) or list(a) != list(b): out.append(('shape', path)); return
        for k in a: diff(a[k], b[k], path + (k,), out)
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b): out.append(('shape', path)); return
        for i, (x, y) in enumerate(zip(a, b)): diff(x, y, path + (i,), out)
    elif key(a) != key(b): out.append(('scalar', path))
def at(v, path):
    for p in path: v = (v.v if isinstance(v, Obj) else v)[p]
    return v

def check(t, un):
    stream = un(t['yaml'])
    app = (un(t['schema']), t['root']) if 'schema' in t else None
    store = {h: un(x).encode('utf-8') for h, x in t['store'].items()} if 'store' in t else None
    limit, cut = t.get('limit', LIMIT), t.get('cut', False)
    ns['DATEHOLD'] = (t['holds'], t.get('leap-second', False), t.get('year-zero', False)) if 'holds' in t else None
    global WR
    ns['BIND'] = tuple(t['bind']) if 'bind' in t else None; WR = t.get('writes') or {}
    docs = read(stream).docs; vals = typed(stream, app, store, limit, cut)
    cs = chunks(stream); slots = [i for i, c in enumerate(cs) if c[0] == 'doc']
    assert len(slots) == len(docs), (t['name'], len(slots), len(docs))
    results = []
    for n, ((name, _), v) in enumerate(zip(docs, vals)):
        before = ''.join(c[1] for c in cs[:slots[n]] if c[0] != 'doc'); W = written(v)
        def back(quote):
            out = before + emit_doc(name, W, quote)
            try: return out, typed(out, app, store, limit, cut)[0], None
            except REFUSED as e: return out, None, e
        # Spell each scalar where it is typed: a string plain if part 1 reads it back, then quoted if the
        # schema reads it as something else, or refuses it; an optional key's null as no value. Learning
        # the type at a place by reading back is this checker's shortcut, and it checks section 13's claim
        # that one respelling changes nothing else.
        quote = set(); before_d = None
        for _ in range(64):
            out, got, err = back(quote)
            if err is not None:
                p = place(W, err)
                if p is None or p in quote or not (quotable(at(W, p)) or at(W, p) is None and p and isinstance(p[-1], str)):
                    results.append(('refused', str(err), out)); break
                quote.add(p); continue
            d = []; diff(v, got, (), d)
            new = {p for k, p in d if k == 'scalar' and p not in quote and (quotable(at(W, p)) or at(W, p) is None and p and isinstance(p[-1], str))}
            if before_d is not None and {p for k, p in d} - before_d - quote:
                results.append(('claim', f'respelling {sorted(map(str, quote))} changed {sorted(map(str, {p for k, p in d} - before_d - quote))}', out)); break
            before_d = {p for k, p in d}
            if new: quote |= new; continue
            if not d: results.append(('ok', f'{len(quote)} respelled' if quote else 'plain', out))
            else: results.append(('refused', '; '.join(f'{"/" + "/".join(map(str, p))} {at(v, p)!r} came back {at(got, p)!r}' if k == 'scalar' else
                                                       f'{"/" + "/".join(map(str, p))} {at(v, p)!r} came back {at(got, p)!r}, not through its name' if k == 'name' else f'shape at {p}' for k, p in d), out))
            break
    return results
def place(v, err):
    """The value a refusal names, by its path (part 2, section 2), or None."""
    m = re.match(r'(/[^:]*): ', str(err))
    if not m: return None
    p = ()
    for step in ([] if m[1] == '/' else m[1].split('/')[1:]):
        if isinstance(v, list) and step.isdigit() and int(step) < len(v): p += (int(step),); v = v[int(step)]
        elif isinstance(v, dict) and step in v: p += (step,); v = v[step]
        else: return None
    return p
if __name__ == '__main__':
    import yaml
    suite = sys.argv[1]
    sd = {'__name__': 'sd'}; exec(open(os.path.join(suite, 'bin', 'suite-to-data'), encoding='utf-8').read().split("\nif __name__")[0], sd)
    un = sd['unescape']; src = os.path.join(suite, 'yes', 'src')
    tally, why = Counter(), Counter(); shown = Counter(); verbose = '-v' in sys.argv; mark = '--mark' in sys.argv; wrong = []
    for f in sorted(os.listdir(src)):
        tests = yaml.safe_load(open(os.path.join(src, f), encoding='utf-8'))
        assert len(tests) == 1, f
        for t in tests:
            if t.get('fail') or t.get('keep') or 'typed' not in t: continue
            tally['tests'] += 1
            res = check(t, un); refused = any(k == 'refused' for k, _, _ in res)
            tally['marked' if refused else 'unmarked'] += 1
            if mark and refused and t.get('emit') != 'refused':
                body = open(os.path.join(src, f), encoding='utf-8').read()
                assert body.count('\n  yaml: |') == 1, f
                open(os.path.join(src, f), 'w', encoding='utf-8').write(body.replace('\n  yaml: |', '\n  emit: refused\n  yaml: |'))
            elif not mark and refused != (t.get('emit') == 'refused'): wrong.append(f'{f}: {"should" if refused else "should not"} be marked emit: refused')
            for kind, msg, out in res:
                tally[kind] += 1; tally['documents'] += 1
                if kind != 'ok':
                    cat = re.sub(r"'[^']*'|\"[^\"]*\"|[0-9]+", '_', msg)[:90]; why[(kind, cat)] += 1
                    if verbose or shown[(kind, cat)] < 2:
                        shown[(kind, cat)] += 1
                        print(f'== {f} {t["name"]}: {kind}: {msg[:300]}'); print('   ' + out.replace('\n', '\n   ')[:600])
    print(dict(tally))
    for (k, c), n in why.most_common(): print(f'{n:5} {k}: {c}')
    for w in wrong: print(w)
    sys.exit(1 if wrong or tally['claim'] else 0)
