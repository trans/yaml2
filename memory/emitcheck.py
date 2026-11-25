"""Write every typed test of part 2's suite out again, as section 13 says, and read it back.

    python3 -I emitcheck.py SUITE [--empty-null] [-v]     (SUITE is the code checkout's suite/ directory)

--empty-null writes an optional key's null as an empty value, as proposed on 2026-11-24; -v shows
every document not written back, not only two of each kind.

A throwaway emitter written from part 2's section 13, not a reference. For each accepted test with
typed events, it types the stream with schemacheck.py, then writes each document from its typed
values alone, as an emitter given typed data would: a string plain where part 1 reads it back as
that text, else double-quoted; every other scalar in its standard spelling (a float as section 4.4
says). No text kept from the reading is used. It reads the result back with the same schema, and
quotes a string that came back as something else. What still comes back different is refused.

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

def key(v):
    """v with its types, to compare: a float by its bits, so the sign of zero counts."""
    if isinstance(v, dict): return ('map', tuple((k, key(x)) for k, x in v.items()))
    if isinstance(v, list): return ('seq', tuple(key(x) for x in v))
    if isinstance(v, Tag): return (v.kind, v.text)
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
        return v.text  # A date, a time, base64 and a decimal are delivered as their text (section 4).
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

EMPTY = '--empty-null' in sys.argv  # The proposed rule: an optional key's null is written as an empty value.
def text(v, path, quote):
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
    """Paths of scalars that differ; ('shape', path) where the trees themselves differ."""
    if isinstance(a, dict):
        if not isinstance(b, dict) or list(a) != list(b): out.append(('shape', path)); return
        for k in a: diff(a[k], b[k], path + (k,), out)
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b): out.append(('shape', path)); return
        for i, (x, y) in enumerate(zip(a, b)): diff(x, y, path + (i,), out)
    elif key(a) != key(b): out.append(('scalar', path))
def at(v, path):
    for p in path: v = v[p]
    return v

def check(t, un):
    stream = un(t['yaml'])
    app = (un(t['schema']), t['root']) if 'schema' in t else None
    store = {h: un(x).encode('utf-8') for h, x in t['store'].items()} if 'store' in t else None
    limit, cut = t.get('limit', LIMIT), t.get('cut', False)
    ns['DATEHOLD'] = (t['holds'], t.get('leap-second', False), t.get('year-zero', False)) if 'holds' in t else None
    docs = read(stream).docs; vals = typed(stream, app, store, limit, cut)
    cs = chunks(stream); slots = [i for i, c in enumerate(cs) if c[0] == 'doc']
    assert len(slots) == len(docs), (t['name'], len(slots), len(docs))
    results = []
    for n, ((name, _), v) in enumerate(zip(docs, vals)):
        before = ''.join(c[1] for c in cs[:slots[n]] if c[0] != 'doc')
        def back(quote):
            out = before + emit_doc(name, v, quote)
            try: return out, typed(out, app, store, limit, cut)[0], None
            except REFUSED as e: return out, None, e
        quote = set(); out, got, err = back(quote)
        if err is None:
            d = []; diff(v, got, (), d)
            fix = {p for k, p in d if k == 'scalar' and isinstance(at(v, p), str) and not isinstance(at(v, p), Tag)}
            if EMPTY: fix |= {p for k, p in d if k == 'scalar' and p and at(v, p) is None and isinstance(p[-1], str)}
            if fix:
                out2, got2, err2 = back(fix)
                if err2 is not None: results.append(('claim', f'quoting {sorted(map(str, fix))} refused the document: {err2}', out2)); continue
                d2 = []; diff(v, got2, (), d2)
                if {p for k, p in d2} - {p for k, p in d}: results.append(('claim', f'quoting {fix} changed {sorted(map(str, {p for k, p in d2} - {p for k, p in d}))}', out2)); continue
                out, got, d = out2, got2, d2
            if not d: results.append(('ok', 'plain' if not fix else f'{len(fix)} quoted', out)); continue
            results.append(('refused', '; '.join(f'{"/" + "/".join(map(str, p))} {at(v, p)!r} came back {at(got, p)!r}' if k == 'scalar' else f'shape at {p}' for k, p in d), out))
        else:
            # A string spelled plain never refuses a document (section 13), so try them all quoted, then refuse.
            q = set(); collect(v, (), q)
            out2, got2, err2 = back(q)
            if err2 is None:
                d2 = []; diff(v, got2, (), d2)
                results.append(('claim', f'plain refused ({err}), all quoted gives {"the same" if not d2 else d2}', out)); continue
            results.append(('refused', str(err), out))
    return results
def collect(v, path, q):
    if isinstance(v, dict):
        for k, x in v.items(): q.add(path + (('key', k),)); collect(x, path + (k,), q)
    elif isinstance(v, list):
        for i, x in enumerate(v): collect(x, path + (i,), q)
    elif isinstance(v, str) and not isinstance(v, Tag): q.add(path)
    elif v is None and EMPTY and path and isinstance(path[-1], str): q.add(path)

if __name__ == '__main__':
    import yaml
    suite = sys.argv[1]
    sd = {'__name__': 'sd'}; exec(open(os.path.join(suite, 'bin', 'suite-to-data'), encoding='utf-8').read().split("\nif __name__")[0], sd)
    un = sd['unescape']; src = os.path.join(suite, 'yes', 'src')
    tally, why = Counter(), Counter(); shown = Counter(); verbose = '-v' in sys.argv
    for f in sorted(os.listdir(src)):
        for t in yaml.safe_load(open(os.path.join(src, f), encoding='utf-8')):
            if t.get('fail') or t.get('keep') or 'typed' not in t: continue
            tally['tests'] += 1
            for kind, msg, out in check(t, un):
                tally[kind] += 1; tally['documents'] += 1
                if kind != 'ok':
                    cat = re.sub(r"'[^']*'|\"[^\"]*\"|[0-9]+", '_', msg)[:90]; why[(kind, cat)] += 1
                    if verbose or shown[(kind, cat)] < 2:
                        shown[(kind, cat)] += 1
                        print(f'== {f} {t["name"]}: {kind}: {msg[:300]}'); print('   ' + out.replace('\n', '\n   ')[:600])
    print(dict(tally))
    for (k, c), n in why.most_common(): print(f'{n:5} {k}: {c}')
