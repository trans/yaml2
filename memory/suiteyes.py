"""Write part 2's suite from schemacheck.py's own tests: each stream they type, with the checker's answer.

    python3 -I .ai/memory/suiteyes.py spec/yaml-easy-schema.md suite          (from the code checkout)
    python3 -I .ai/memory/suiteyes.py --check spec/yaml-easy-schema.md suite  (reads it back, needs PyYAML)

Runs the checker's tests with typed() and Schema() recorded, and writes one file per test to
suite/yes/src, replacing what is there. Every test of the checker passes, so each answer is also what
the test expected. A stream is also read with part 1's size limit, which typed() leaves out, and a test
whose limit part 1 would refuse the stream at is left out and counted. The format is in
suite/yes/README.md.
"""
import base64, collections, json, os, re, sys, textwrap
here = os.path.dirname(os.path.abspath(__file__))
CHECK = sys.argv[1] == '--check'
specfile, suite = sys.argv[2:4] if CHECK else sys.argv[1:3]
sn = {'__name__': 'sn', '__file__': here + '/suitenew.py'}
exec(open(here + '/suitenew.py', encoding='utf-8').read().split("\nif __name__ == '__main__':")[0], sn)
esc, field, quoted, ident, ESCAPED = (sn[k] for k in 'esc field quoted ident ESCAPED'.split())
# A tag line that YAML 1.1 or 1.2 would read as something other than a string, such as the tag `null` alone.
def plain(t): return f"'{t}'" if t.lower() in ('null', '~', 'true', 'false', 'yes', 'no', 'on', 'off', 'y', 'n') else t
whole = open(here + '/schemacheck.py', encoding='utf-8').read()
src, main = whole.split("\nif __name__ == '__main__':")
ns = {'__name__': 'sc', '__file__': here + '/schemacheck.py'}
exec(compile(src, here + '/schemacheck.py', 'exec'), ns)
REFUSED, LIMIT, No, SchemaCls, typed0, read0 = (ns[k] for k in 'REFUSED LIMIT No Schema typed read'.split())
framed = ns['g']['framed']
state = {'tag': False, 'depth': 0}

class Tag:
    """A typed scalar the checker gives as a str or an int: the type, and the text a harness compares."""
    def __init__(s, kind, text): s.kind, s.text = kind, text
scalar0 = SchemaCls.scalar
def scalar(s, name, lim, v, path):
    out = scalar0(s, name, lim, v, path)
    if not state['tag']: return out
    if name in ('date', 'datetime', 'binary'): return Tag(name, out)
    if name == 'bigint': return Tag(name, str(out))
    if name == 'decimal': return Tag(name, ns['canon'](str(v)) if lim and lim[1] else str(v))
    return out
SchemaCls.scalar = scalar

records = []
def line():
    f = sys._getframe(2)
    while f and not (f.f_code.co_filename == '<main>' and f.f_code.co_name == '<module>'): f = f.f_back
    return f.f_lineno if f else 0
def outcome(fn):
    state['tag'] = True; state['depth'] += 1
    try: return ('ok', fn())
    except REFUSED as e: return ('fail', e)
    finally: state['tag'] = False; state['depth'] -= 1
def record(at, stream, app, store, limit, cut, keep):
    res = outcome(lambda: typed0(stream, app, store, limit, cut, keep))
    records.append(dict(line=at, stream=stream, app=app, store=store, limit=limit, cut=cut, keep=keep, hold=ns['DATEHOLD'], res=res))
    return res
def typed(stream, app=None, store=None, limit=LIMIT, cut=False, keep=False):
    if state['depth'] == 0: record(line(), stream, app, store, limit, cut, keep)
    state['depth'] += 1
    try: return typed0(stream, app, store, limit, cut, keep)
    finally: state['depth'] -= 1
texts = {}
def read(t, *a, **k):
    r = read0(t, *a, **k)
    if state['depth'] == 0: texts[id(r.table)] = (t, r.table)
    return r
def Schema(table, root, cut=False, limit=LIMIT, kept=False):
    """A schema loaded on its own is an application's schema with its root, over a stream with no
    documents. The same outcome through typed() is checked."""
    if state['depth'] == 0 and id(table) in texts:
        direct = outcome(lambda: SchemaCls(table, root, cut, limit, kept))
        res = record(line(), '%YAML 2.0\n', (texts[id(table)][0], root), None, limit, cut, kept)
        if (direct[0], type(direct[1])) != (res[0], type(res[1])) and not (direct[0] == res[0] == 'ok'):
            sys.exit(f'Schema() and typed() differ on {root}: {direct} {res}')
    state['depth'] += 1
    try: return SchemaCls(table, root, cut, limit, kept)
    finally: state['depth'] -= 1
ns['typed'], ns['read'], ns['Schema'] = typed, read, Schema

if not CHECK:
    # The checker's tests, with the same line numbers as in schemacheck.py.
    sys.argv = [here + '/schemacheck.py', specfile]
    code = compile('\n' * (src.count('\n') + 1) + textwrap.dedent(main), '<main>', 'exec')
    out = sys.stdout; sys.stdout = log = __import__('io').StringIO()
    try: exec(code, ns)
    except SystemExit as e: status = e.code
    else: status = 0
    sys.stdout = out
    if status: sys.exit('the checker fails:\n' + log.getvalue())
    print(log.getvalue().strip())

    # Section 11's typed count. The checker tests it with limits below the stream's held size, which
    # part 1 counts with the table, so no parser could pass them. Here each of its streams is scaled (a
    # 400-character string, a 400-character key) and tested at the lowest limit that both held and typed
    # allow, and, where typed is the one that binds, at one less. The checker's 1 MB test is too large for
    # the suite, so its form with 1,000 types of a 1 KB string is here too, and the same with one type.
    ns['DATEHOLD'] = None
    S = 'abcdefgh' * 50; K = 'x' * 400; kb = 'a' * 1000; refs = '[' + ', '.join(['*s'] * 1000) + ']\n'
    S11 = f'--- &\ns: {S}\none: [!str, ...]\nthree: [!str(/a.*/), !str(/.*h/), !str(1..)]\n'
    X11 = f'--- &\nx: {{n: {S}}}\njob: {{n: !str}}\n'
    COUNTS = [(S11 + '--- !one\n[*s, *s, *s]\n', None), (S11 + '--- !three\n[*s, *s, *s]\n', None),
              (X11 + 'pair: {a: !job, b: !job}\n--- !pair\n{a: *x, b: *x}\n', None),
              (X11 + 'pair: {a: {n: !str}, b: {n: !str}}\n--- !pair\n{a: *x, b: *x}\n', None),
              (X11 + f'pair: {{a: !job, b: !job}}\n--- !pair\n{{a: {{n: {S}}}, b: {{n: {S}}}}}\n', None),
              (f'--- &\nv: {{{K}: 1}}\nleaf: {{}}\nroot:\n  a:\n    child: !leaf\n    !**: !int\n  b:\n    child: !leaf\n    !**: !str\n--- !root\na:\n  child: *v\nb:\n  child: *v\n', None),
              (f'--- &\nv: {{{K}: 1}}\nroot:\n  !**: !int\n--- !root\na: *v\nb: *v\n', None),
              (f'--- &\nv: {{k{"1" * 400}: 1}}\nroot:\n  !**:\n    !str(/k.*/): !int\n--- !root\na: *v\nb: *v\n', None),
              (f'--- &\ns: {S}\n---\n[*s, *s, *s]\n---\n[*s, *s, *s]\n', ('--- &\none: [!str, ...]\n', 'one')),
              ('--- &\ns: ' + kb + '\nrow: [' + ', '.join(f'!str({k}..)' for k in range(1, 1001)) + ']\n--- !row\n' + refs, None),
              ('--- &\ns: ' + kb + '\nrow: [!str, ...]\n--- !row\n' + refs, None)]
    def lowest(ok):
        lo, hi = 0, 1
        while not ok(hi): hi *= 2
        while lo < hi:
            m = (lo + hi) // 2
            if ok(m): hi = m
            else: lo = m + 1
        return lo
    def held_ok(st, n):
        try: read0(st, n, False, True); return True
        except No: return False
    def typed_ok(st, app, n):
        state['depth'] += 1
        try: typed0(st, app, None, n, False, True); return True
        except REFUSED: return False
        finally: state['depth'] -= 1
    bounds = []
    for st, app in COUNTS:
        h = lowest(lambda n: held_ok(st, n)); t = lowest(lambda n: typed_ok(st, app, n)); L = max(h, t)
        bounds.append((h, t)); record(-1, st, app, None, L, False, True)
        if t > h: record(-1, st, app, None, t - 1, False, True)
    print('typed tests, (held, typed):', bounds)

lines = whole.split('\n')
def group(n):
    """The list a test comes from: the nearest enclosing `for`, or the line itself."""
    if n < 0: return 'extra'
    ind = len(lines[n - 1]) - len(lines[n - 1].lstrip())
    for k in range(n - 2, 0, -1):
        l = lines[k]; i = len(l) - len(l.lstrip())
        if l.strip() and i < ind:
            m = re.match(r'\s*for .+? in ([A-Za-z_][A-Za-z_0-9]*)\s*:', l)
            if m: return m[1]
            if re.match(r'\s*for ', l): return f'line {k + 1}'
            if i <= 4: return f'line {n}'
            ind = i
    return f'line {n}'
first = next(i for i, l in enumerate(lines, 1) if 'blocks = list(re.finditer' in l)
last = next(i for i, l in enumerate(lines, 1) if "print(f'spec examples" in l)

spec = open(specfile, encoding='utf-8').read()
heads = [(m.start(), m[1], m[2]) for m in re.finditer(r'^#{2,3} ([0-9.]+?)\.? (.+)$', spec, re.M)]
def heading(body):
    i = spec.find('\n' + body + '```')
    h = [x for x in heads if x[0] < i]
    return (h[-1][1], h[-1][2].replace('`', '')) if i >= 0 and h else ('?', '?')

# Where each list's tests come from in part 2, and what they are about. None: by what the test holds.
GROUPS = {
    'good': (None, 'A standard type'), 'no': (None, 'A standard type'), 'schemas': (None, 'A schema refused'),
    'ints': ('4.5', 'A pattern on !int'), 'notints': ('4.5', 'A pattern on !int'),
    'forms': ('4.3', 'A pattern is a plain scalar'), 'says': ('3', 'Who says how to read a document'),
    'unions': ('9', 'Alternatives'), 'star': (None, 'Keys not named'), 'notstar': (None, 'Keys not named'),
    'badstar': (None, 'A schema refused'), 'pub': ('3.1', 'A published name'), 'notpub': ('3.1', 'A published name'),
    'reach': ('2', 'What the root reaches'), 'nums': ('4.4', 'Numbers'), 'nope': ('4.4', 'Numbers'),
    'bounds': ('4.2', 'A limit on the number as written'), 'outside': ('4.2', 'A limit on the number as written'),
    'hard': ('4.4', 'The nearest binary64'), 'floats': ('4.4', 'Floats'), 'floatnot': ('4.4', 'Floats'),
    'gone': ('4.4', 'A float width or round'), 'decs': ('4.5', 'A pattern on !decimal'), 'decnot': ('4.5', 'A pattern on !decimal'),
    'more': (None, 'Patterns, precision and limits'), 'morenot': (None, 'Patterns, precision and limits'),
    'fulls': ('9', "A schema's full size"), 'emptyseq': ('6', 'An empty sequence'),
    'goods3': (None, 'From the third review'), 'bads3': (None, 'From the third review'), 'schemas3': (None, 'A schema refused'),
    'loads3': (None, 'A schema that loads'), 'counts': ('11', 'Typed'), 'goodsP': ('4.8', 'Dates'), 'badsP': ('4.8', 'Dates'),
    'oks': ('4.8', 'What a parser holds of a date'), 'nos': ('4.8', 'What a parser holds of a date'),
    'schemasP': ('4.8', 'A date level or round'), 'loadsP': (None, 'A schema that loads'), 'extra': ('11', 'Typed'),
}
# Tests outside a list, found by what their line holds.
SINGLES = [('DIFFERS renamed', '8', "The names are the author's"), ('QUOTED PATTERN NOT A LITERAL', '5', 'A quoted pattern is a literal'),
           ('doubling(', '9', 'Names that double'), ('read(chain)', '9', "A schema's full size"), ('read(wide)', '9', 'Unions at the ceiling'),
           ('a stamp past the limit', '9', "A schema's full size"), ('pub3(', '3.1', 'A published schema'), ("for t in ('retries: abc", '3', 'Who says how to read a document'),
           ('for z3 in', '4.4', 'The sign of zero'), ('for body3 in', '3.1', 'A published schema is one table'), ('many', '11', 'Typed'), ('app=app2', '11', 'Typed')]
def single(g):
    l = lines[int(g[5:]) - 1]
    return next(((sec, title) for k, sec, title in SINGLES if k in l), (None, None))
def section(r):
    """Part 2's section for a test, by what it holds, where its list doesn't say."""
    t = tagtext(r)[0]
    if r['store'] is not None: return '3.1'
    if r['keep']: return '11'
    if r['app']: return '3'
    if '!**' in t: return '10'
    if re.search(r'!\*(?!\*)', t): return '7'
    if '<<' in t: return '11'
    if re.search(r'!date(time)?\b', t): return '4.8'
    if re.search(r'!decimal\([0-9]+:[0-9]+ ', t): return '4.7'
    if re.search(r'!decimal\([0-9]+:', t): return '4.6'
    if re.search(r'!(int|bigint|float|decimal|null)\([^\n]*/', t): return '4.5'
    if re.search(r'!str\([^\n]*/', t): return '4.3'
    if re.search(r'\([^\n)]*\.\.', t): return '4.2'
    if re.search(r'!(int|bigint|float|decimal)\b', t): return '4.4'
    if ' | ' in t: return '9'
    if re.search(r'!(binary|bool|null|str|any)\b', t): return '4.1'
    return '14'
TYPES = ('str', 'int', 'bigint', 'float', 'decimal', 'bool', 'null', 'any', 'date', 'datetime', 'binary')
TABLE = re.compile(r'^--- &[ \t]*\n((?:(?!---|\.\.\.).*\n?)*)', re.M)
def chunks(text):
    """A table's entries, by key: each one's lines, from its key to the next key at the margin."""
    out = {}; cur = None
    for l in text.split('\n'):
        if l and l[0] not in ' \t#':
            m = re.match(r'("(?:[^"\\]|\\.)*"|\'(?:[^\']|\'\')*\'|[^:]*?)\s*:(?:[ \t]|$)', l)
            if m:
                k = m[1]
                try: k = json.loads(k) if k.startswith('"') else k[1:-1].replace("''", "'") if k.startswith("'") else k
                except ValueError: pass
                cur = k; out[cur] = l + '\n'; continue
        if cur is not None: out[cur] += l + '\n'
    return out
def reaches(table, root):
    sc = SchemaCls.__new__(SchemaCls)
    try: SchemaCls.__init__(sc, table, root)
    except Exception: pass
    return getattr(sc, 'reached', {root})
def tagtext(r):
    """What a test asks of a parser: the entries its roots reach, its documents, and any published
    file, rather than the whole table, since an entry nothing reaches isn't a type (section 2)."""
    st = r['stream']; store = ''.join((r['store'] or {}).values())
    try: rr = read0(st)
    except No: return st + (r['app'][0] if r['app'] else '') + store, st
    parts = TABLE.findall(st); ch = {k: v for p in parts for k, v in chunks(p).items()}
    docs = TABLE.sub('', st); names = set()
    for name, _ in rr.docs:
        if name and '/' not in name and name in rr.table: names |= reaches(rr.table, name)
    if not rr.docs: names = set(ch)
    schema = ''.join(ch.get(k, ''.join(parts)) for k in names)
    if r['app']:
        ach = chunks(TABLE.findall(r['app'][0] + '\n')[0] if TABLE.findall(r['app'][0] + '\n') else r['app'][0])
        schema += ''.join(ach.get(k, r['app'][0]) for k in reaches(read0(r['app'][0]).table, r['app'][1]))
    return docs + schema + store, schema + store
def tags(r, sec, fail):
    t, table = tagtext(r)
    out = []
    if r['line'] in range(first, last): out.append('spec')
    out += [n for n in TYPES if re.search(rf'!{n}(?![A-Za-z0-9_-])', t)]
    if re.search(r'!(str|int|bigint|float|decimal|null)\([^\n]*/', t): out.append('pattern')
    if re.search(r'\([^\n)]*\.\.', t): out.append('range')
    if re.search(r'!decimal\([^\n)]*[0-9]:[0-9]', t): out.append('precision')
    if ' | ' in t: out.append('union')
    if '[' in table: out.append('sequence')
    if re.search(r'!\*(?!\*)', t): out.append('star')
    if '!**' in t: out.append('double-star')
    if '<<' in t: out.append('merge')
    if re.search(r'(^|[ \[,{])\*[^\s,\]}]', t, re.M): out.append('reference')
    if r['store'] is not None or re.search(r'--- !\S+\.yes#', t): out.append('published')
    if r['app']: out.append('application')
    if r['keep']: out.append('typed')
    if r['cut']: out.append('cut')
    if r['hold']: out.append('holds')
    else:
        # Without holds, a test is for a parser that holds every time. These say what more it needs than
        # 9 fraction digits, the most a common language holds, so one that holds less can skip it.
        docs = TABLE.sub('', r['stream'])
        if re.search(r'!datetime', t) and re.search(r'[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{10,}', docs): out.append('long-fraction')
        if re.search(r'!datetime', t) and re.search(r'[Tt][0-9]{2}:[0-9]{2}:60', docs): out.append('second-60')
        if re.search(r'!date(time)?\b', t) and re.search(r'(^|[^0-9])0000-[0-9]{2}-[0-9]{2}', docs): out.append('year-0000')
    if r['limit'] != LIMIT: out.append('size')
    if not out or out == ['error']: out.insert(0, 'schema')
    if fail: out.append('error')
    return ' '.join(dict.fromkeys(out))

EV = {'date': 'DATE', 'datetime': 'DATETIME', 'binary': 'BIN', 'bigint': 'BIG', 'decimal': 'DEC'}
def scal(v):
    if isinstance(v, Tag): return EV[v.kind], base64.b64decode(v.text).hex() if v.kind == 'binary' else v.text
    if v is None: return 'NULL', None
    if isinstance(v, bool): return 'BOOL', 'true' if v else 'false'
    if isinstance(v, int): return 'INT', str(v)
    if isinstance(v, float): return 'FLT', repr(v)
    if isinstance(v, str): return 'VAL', v
    raise TypeError(repr(v))
def events(docs):
    ev = ['+STR']
    def node(v, d):
        if isinstance(v, list): ev.append(' ' * d + '+SEQ'); [node(x, d + 1) for x in v]; ev.append(' ' * d + '-SEQ')
        elif isinstance(v, dict):
            ev.append(' ' * d + '+MAP')
            for k, x in v.items(): node(k, d + 1); node(x, d + 1)
            ev.append(' ' * d + '-MAP')
        else:
            k, text = scal(v); ev.append(' ' * d + f'={k}' + ('' if text is None else ' :' + esc(text)))
    for name, v in docs: ev.append(' +DOC' + (' !' + esc(name) if name else '')); node(v, 2); ev.append(' -DOC')
    return '\n'.join(ev + ['-STR']) + '\n'
def jstr(s): return ''.join(f'\\u{ord(c):04x}' if ESCAPED.match(c) else c for c in json.dumps(s, ensure_ascii=False))
def js(v):
    if isinstance(v, Tag): return v.text if v.kind in ('bigint', 'decimal') else jstr(v.text)
    if v is None: return 'null'
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, (int, float)): return repr(v)
    if isinstance(v, str): return jstr(v)
    if isinstance(v, list): return '[' + ', '.join(js(x) for x in v) + ']'
    return '{' + ', '.join(jstr(k) + ': ' + js(x) for k, x in v.items()) + '}'
def entry(stream, name):
    m = re.search(rf'^{re.escape(name)}: *(.*)$', stream, re.M)
    return m[1] if m and m[1] else None
def short(t, n=60):
    t = esc(t.strip())
    return t if len(t) <= n else t[:n - 1] + '…'
def describe(r):
    st = r['stream']
    m = re.search(r'(?:\A|\n)--- !(\S+)\n((?:.|\n)*?)\Z', st)
    if r['app'] and not r['app'][0].count('\n--- !') and st.strip() == '%YAML 2.0':
        body = re.sub(r'\A(%YAML 2.0\n)?--- &\n', '', r['app'][0])
        return f'the schema `{short(body.rstrip(chr(10)).replace(chr(10), "; "), 50)}` from `{r["app"][1]}`'
    if m:
        ty = entry(st, m[1])
        doc = short(m[2].rstrip('\n').replace('\n', '; '), 40)
        return f'`{short(ty, 40)}` on `{doc}`' if ty else f'`!{short(m[1], 30)}` on `{doc}`'
    body = re.sub(r'\A(%YAML 2.0\n)?--- &\n', '', st)
    return f'`{short(body.rstrip(chr(10)).replace(chr(10), "; "), 60)}`'
def refused(r, e):
    """Where the refusal comes from, for a harness that can tell: the schema, a document, or the stream."""
    name = type(e).__name__
    if name == 'SchemaError': return 'schema', None
    if name == 'No':
        if 'typed passes the size limit' in str(e): return 'document', str(e).split(': ')[0]
        try: read0(r['stream']); return 'schema', None
        except No: return 'stream', None
    m = re.match(r'(/[^:]*): ', str(e))
    return 'document', m[1] if m else None

# Part 1's size limit on the stream itself, which typed() doesn't apply.
def part1(r):
    try: read0(r['stream'], None if r['limit'] == LIMIT else r['limit'], False, r['keep']); return True
    except No: return False

if not CHECK:
    taken = {f[:-5] for f in os.listdir(os.path.join(suite, 'src'))}
    dest = os.path.join(suite, 'yes', 'src'); os.makedirs(dest, exist_ok=True)
    for f in os.listdir(dest):
        if f.endswith('.yaml'): os.remove(os.path.join(dest, f))
    # A stream with a table and no document: the checker loads every entry, but section 2 says an entry
    # nothing reaches isn't a type, so a parser accepts it. Each such test gets a document stamped with an
    # entry, and keeps the checker's answer only if the schema is still refused, or still loads.
    CANDS = ['x', '0', '1', '0.5', 'a', 'b', 'true', 'null', '2001-02-03', '2001-02-03T04:05:06Z', 'aGk=', '[]', '{}', 'x' * 1024, 'ab' * 256]
    def reached(r):
        try: rr = read0(r['stream'])
        except No: return r
        if rr.docs or not rr.table or r['app'] or r['store'] is not None: return r
        refused = r['res'][0] == 'fail' and type(r['res'][1]).__name__ == 'SchemaError'
        if not refused and r['line'] in range(first, last): return r  # An example that loads stays as written.
        later = None
        for k in rr.table:
            for v in CANDS:
                st = r['stream'] + ('' if r['stream'].endswith('\n') else '\n') + f'--- !{k}\n{v}\n'
                res = outcome(lambda: typed0(st, None, None, r['limit'], r['cut'], r['keep']))
                schema = res[0] == 'fail' and type(res[1]).__name__ == 'SchemaError'
                if refused and schema or not refused and res[0] == 'ok': return dict(r, stream=st, res=res)
                if not refused and not schema and later is None: later = dict(r, stream=st, res=res)
        return later
    conv = collections.Counter(); lost = []; seen = set(); count = collections.Counter(); skipped = collections.Counter(); per = collections.Counter(); n = 0
    for r in records:
        r0 = r; r = reached(r)
        if r is not r0 and r0['line'] in range(first, last): print('  spec example given a document:', repr(r0['stream'][:80]), '->', type(r['res'][1]).__name__ if r and r['res'][0] == 'fail' else r and r['res'][0])
        if r is not r0 and r is not None: conv[r0['res'][0] + ('' if r['res'][0] == r0['res'][0] else ' -> ' + r['res'][0])] += 1
        if r is None: skipped['no document reaches what the checker refuses'] += 1; continue
        key = json.dumps([framed(r['stream']), r['app'], sorted((r['store'] or {}).items()) if r['store'] is not None else None,
                          r['limit'], r['cut'], r['keep'], r['hold']], default=lambda b: b.decode('utf-8', 'surrogatepass'))
        if key in seen: skipped['the same as another'] += 1; continue
        seen.add(key)
        if r['store']: r['store'] = {h: b.decode('utf-8') for h, b in r['store'].items()}
        if len(r['stream']) > 200000: skipped['over 200 KB'] += 1; continue
        ok = r['res'][0] == 'ok'
        if not part1(r):
            if ok: skipped["refused by part 1's limit, accepted by typed()"] += 1; lost.append(r); continue
        g = 'spec' if r['line'] in range(first, last) else group(r['line'])
        if g == 'spec':
            sec, title = heading(r0['stream'].rstrip('\n') + '\n')
            per[sec] += 1; name = f'{title}, example {per[sec]}'
        else:
            sec, title = single(g) if g.startswith('line ') else GROUPS.get(g, (None, None))
            if title is None: sys.exit(f'no group for line {r["line"]} ({g})')
            sec = sec or section(r); name = f'{title}: {describe(r)}'
            if r['keep'] and r['limit'] != LIMIT: name += f', at a limit of {r["limit"]}'
        fail = not ok
        t = ['---', f'- name: {quoted(name)}', f'  from: part 2, section {sec}', f'  tags: {plain(tags(r, sec, fail))}']
        if fail:
            t.append('  fail: true')
            where, at = refused(r, r['res'][1])
            if not part1(r): where, at = None, None  # Part 1's limit and the schema both refuse it.
            if where: t.append(f'  refused: {where}')
            if at: t.append(f'  at: {quoted(at)}')
        if r['limit'] != LIMIT: t.append(f"  limit: {r['limit']}")
        if r['keep']: t.append('  keep: true')
        if r['app']:
            t += field('schema', framed(r['app'][0])); t.append(f"  root: {quoted(r['app'][1])}")
        if r['store'] is not None:
            if not r['store']: t.append('  store: {}')
            else:
                t.append('  store:')
                for h, b in r['store'].items(): t += ['  ' + l if l else l for l in field(f"'{h}'", b)]
        if r['cut']: t.append('  cut: true')
        if r['hold']:
            d, leap, y0 = r['hold']; t.append(f'  holds: {d}')
            if leap: t.append('  leap-second: true')
            if y0: t.append('  year-zero: true')
        t += field('yaml', framed(r['stream']))
        if not fail and not r['keep']:  # As in part 1, a test with keep checks only that the stream is accepted.
            docs = read0(r['stream']).docs
            t += field('typed', events(list(zip([d[0] for d in docs], r['res'][1]))))
            t += field('json', ''.join(js(v) + '\n' for v in r['res'][1]))
        i = ident('yes\0' + key, taken); taken.add(i)
        with open(os.path.join(dest, i + '.yaml'), 'w', encoding='utf-8') as f: f.write('\n'.join(t) + '\n')
        n += 1; count['refused' if fail else 'accepted'] += 1; count['spec' if g == 'spec' else 'edge'] += 1
    print('given a document:', dict(conv))
    print(f'{len(records)} recorded, {n} written: {dict(count)}; left out: {dict(skipped)}')
    for r in lost: print('  left out:', group(r['line']), 'limit', r['limit'], 'keep' if r['keep'] else '', repr(r['stream'][-50:]))

if CHECK:
    # Read each test as a harness would, through suite-to-data's reading of the marks, and run it.
    import yaml
    sd = {'__name__': 'sd'}; exec(open(os.path.join(suite, 'bin', 'suite-to-data'), encoding='utf-8').read().split("\nif __name__")[0], sd)
    un = sd['unescape']; dest = os.path.join(suite, 'yes', 'src'); n = bad = 0
    for f in sorted(os.listdir(dest)):
        for t in yaml.safe_load(open(os.path.join(dest, f), encoding='utf-8')):
            n += 1; why = []
            r = dict(line=0, stream=un(t['yaml']), app=(un(t['schema']), t['root']) if 'schema' in t else None,
                     store={h: un(x).encode('utf-8') for h, x in t['store'].items()} if 'store' in t else None,
                     limit=t.get('limit', LIMIT), cut=t.get('cut', False), keep=t.get('keep', False),
                     hold=(t['holds'], t.get('leap-second', False), t.get('year-zero', False)) if 'holds' in t else None)
            ns['DATEHOLD'] = r['hold']
            res = outcome(lambda: typed0(r['stream'], r['app'], r['store'], r['limit'], r['cut'], r['keep'])) if part1(r) else ('fail', No('part 1'))
            if t.get('fail'):
                if res[0] == 'ok': why.append('accepted')
                elif 'refused' in t and refused(r, res[1]) != (t['refused'], t.get('at')): why.append(f'refused {refused(r, res[1])}')
            elif res[0] != 'ok': why.append(f'refused: {res[1]}')
            elif 'typed' in t:
                docs = read0(r['stream']).docs
                if events(list(zip([d[0] for d in docs], res[1]))) != un(t['typed']): why.append('typed differs')
                if ''.join(js(v) + '\n' for v in res[1]) != un(t['json']): why.append('json differs')
            if why: bad += 1; print(f, t['name'], '; '.join(why))
    print(f'part 2 suite: {n} tests, {bad} fail')
    sys.exit(1 if bad else 0)
