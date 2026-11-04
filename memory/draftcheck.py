"""Test spec/yaml-2.0.md: a throwaway parser written from its grammar. Not a reference.

    python3 -I draftcheck.py SPEC

Runs every example in the draft, then edge cases. The size limit isn't implemented.
"""
import json, re, sys
class No(Exception): pass
FLOWI = ',[]{}'
IND = ",[]{}#&*|>'\""
class P:
    def __init__(s, t):
        if '\r' in t.replace('\r\n', ''): raise No('lone CR')
        if re.search('[^\t\n\r\x20-\x7e\x85\xa0-\ud7ff\ue000-\ufefe\uff00-\ufffd\U00010000-\U0010ffff]', t): raise No('character not allowed')
        s.t = t.replace('\r\n', '\n'); s.i = 0; s.table = {}; s.docs = []; s.td = None; s.stopped = None
    def ch(s, k=0): return s.t[s.i + k] if s.i + k < len(s.t) else ''
    def eof(s): return s.i >= len(s.t)
    def bad(s, m):
        ln = s.t.count('\n', 0, s.i) + 1
        raise No(f'{m} at line {ln}')
    def col(s): return s.i - (s.t.rfind('\n', 0, s.i) + 1)
    def bol(s): return s.i == 0 or s.t[s.i - 1] == '\n'
    def spaces(s):
        n = 0
        while s.ch() == ' ': s.i += 1; n += 1
        return n
    def white(s):
        n = 0
        while s.ch() in (' ', '\t') and s.ch(): s.i += 1; n += 1
        return n
    def eol(s):
        j = s.i; n = s.white()
        if n and s.ch() == '#':
            while s.ch() not in ('\n', ''): s.i += 1
        if s.ch() == '\n': s.i += 1
        elif not s.eof(): s.i = j; s.bad('expected end of line')
    def gap(s):
        while True:
            j = s.i; s.spaces()
            if s.ch() == '#':
                while s.ch() not in ('\n', ''): s.i += 1
            if s.ch() == '\n': s.i += 1
            elif s.eof(): return
            else: s.i = j; return
    def line_is(s, m):
        if not s.bol() or not s.t.startswith(m, s.i): return False
        k = s.i + 3
        return k >= len(s.t) or s.t[k] in ' \t\n'
    def marker(s): return s.line_is('---')
    def dots(s): return s.line_is('...')
    def directive_then_marker(s):
        if not s.t.startswith('%YAML 2.0', s.i): return False
        j = s.i
        try:
            s.i += 9; s.eol(); s.gap(); return s.marker()
        except No: return False
        finally: s.i = j
    def stream(s):
        if not s.t.startswith('%YAML 2.0'): s.bad('no directive')
        s.i = 9; s.eol(); s.gap()
        if not s.eof() and not s.marker() and not s.dots() and not s.directive_then_marker():
            s.docs.append((None, s.node(-1, top=True)))
        while True:
            s.gap()
            if s.eof(): return s
            if s.dots():
                s.i += 3; s.eol(); after = s.i
                while True:
                    j = s.i; s.spaces()
                    if s.ch() == '\n': s.i += 1
                    else: s.i = j; break
                if s.eof(): return s
                if not (s.marker() or s.directive_then_marker()):
                    s.stopped = after; return s
                s.table = {}
            if s.directive_then_marker():
                s.i += 9; s.eol(); s.gap()
            if not s.marker(): s.bad('expected a marker')
            s.document()
    def document(s):
        s.i += 3; j = s.i; n = s.spaces()
        if n and s.ch() == '&':
            s.i += 1; s.eol(); s.gap(); s.tablemap(); return
        name = None
        if n and s.ch() == '!':
            s.i += 1; b = s.i
            while re.match(r'[A-Za-z0-9._/-]', s.ch() or ' '): s.i += 1
            name = s.t[b:s.i]
            if not name: s.bad('no name')
            j = s.i; n = s.spaces()
        if n and s.ch() not in ('#', '\n', ''):
            s.docs.append((name, s.line_node(0)))
        else:
            s.i = j; s.eol(); s.gap(); s.docs.append((name, s.node(-1, top=True)))
    def tablemap(s):
        s.td = 0; here = set()
        while True:
            s.gap()
            if s.eof() or s.marker() or s.dots() or s.ch() == '%': break
            if s.ch() == ' ': s.bad('table entries are at column 0')
            if s.t.startswith('<<:', s.i): s.bad('merge outside an entry')
            k = s.key(); s.colon()
            if k in here: s.bad('key repeated in one table document')
            here.add(k)
            s.table[k] = s.value(0, True)
            s.gap()
        s.td = None
    def is_seq(s):
        c = s.ch()
        if c != '-': return False
        n = s.ch(1)
        if n in (' ', '\t', '\n', ''): return True
        return bool(re.match(r'-<< +\*', s.t[s.i:s.i + 40]))
    def is_map(s):
        j = s.i
        try:
            if s.t.startswith('<<:', s.i) and s.ch(3) in (' ', '\n', ''): return True
            s.key(); s.spaces()
            return s.ch() == ':' and s.ch(1) in (' ', '\t', '\n', '')
        except No: return False
        finally: s.i = j
    def indent_here(s):
        j = s.i; n = s.spaces(); s.i = j; return n
    def node(s, n, top=False):
        s.gap()
        if s.eof() or s.marker() or s.dots(): return ''
        m = s.indent_here()
        if m <= n: return ''
        s.i += m
        if s.is_seq(): return s.seq(m)
        if s.is_map(): return s.map(m)
        return s.line_node(max(n, 0))
    def at(s, m):
        """At an entry for indent m: mid-line at that column, or a line indented m."""
        if s.eof(): return False
        if s.bol():
            if s.marker() or s.dots() or s.directive_then_marker(): return False
            if s.indent_here() != m: return False
            s.i += m; return True
        return s.col() == m
    def enter(s):
        if s.td is not None: s.td += 1
    def leave(s):
        if s.td is not None: s.td -= 1
    def map(s, m):
        s.enter(); out = {}; written = set(); started = False
        while True:
            j = s.i
            if not s.at(m): s.i = j; break
            if s.t.startswith('<<:', s.i) and s.ch(3) in (' ', '\n', ''):
                if started: s.bad('merge after a key')
                if s.td is not None and s.td != 1: s.bad('merge deep in the table')
                s.i += 3
                if not s.spaces(): s.bad('merge needs a reference')
                src = s.ref(False); s.eol()
                if not isinstance(src, dict): s.bad('merge needs a mapping')
                for k, v in src.items(): out[k] = v
            else:
                if not s.is_map(): s.bad('expected a key')
                k = s.key(); s.colon()
                if k in written: s.bad('duplicate key')
                written.add(k); started = True
                out[k] = s.value(m, True)
            s.gap()
        s.leave(); return out
    def key(s):
        c = s.ch()
        if c == '"': return s.double()
        if c == "'": return s.single()
        k = s.plain(False)
        if k == '<<': s.bad('plain << key')
        return k
    def colon(s):
        s.spaces()
        if s.ch() != ':': s.bad('expected :')
        s.i += 1
    def value(s, m, inmap):
        j = s.i; n = s.spaces()
        if n and s.ch() not in ('#', '\n', ''): return s.line_node(m)
        s.i = j
        s.eol(); s.gap()
        if s.eof() or s.marker() or s.dots(): return ''
        k = s.indent_here()
        if inmap and k == m:
            s.i += k
            if s.is_seq(): return s.seq(m)
            s.i -= k
        return s.node(m)
    def seq(s, m):
        s.enter(); out = []
        while True:
            j = s.i
            if not s.at(m): s.i = j; break
            if not s.is_seq(): s.i = j; break
            if s.ch(1) == '<':
                if s.td is not None and s.td != 1: s.bad('merge deep in the table')
                s.i += 3; s.spaces(); src = s.ref(False); s.eol()
                if not isinstance(src, list): s.bad('-<< needs a sequence')
                out += src
            else:
                s.i += 1; k0 = s.i; k = s.spaces()
                if k and s.ch() not in ('#', '\n', ''):
                    if s.is_seq(): out.append(s.seq(s.col()))
                    elif s.is_map(): out.append(s.map(s.col()))
                    else: out.append(s.line_node(m))
                else:
                    s.i = k0; s.eol(); s.gap(); out.append(s.node(m))
            s.gap()
        s.leave(); return out
    def line_node(s, n):
        c = s.ch()
        if c in '|>' and c: return s.block(n)
        if c in '[{' and c: v = s.flow()
        elif c == '*': v = s.ref(False)
        elif c == '"': v = s.double()
        elif c == "'": v = s.single()
        else: v = s.plain(False)
        s.eol(); return v
    def plain(s, flow):
        c, n = s.ch(), s.ch(1)
        if re.match(r'-<< +\*', s.t[s.i:s.i + 40]): s.bad('-<< outside a sequence')
        if not c or c in IND or c in ' \t\n': s.bad('bad start of a plain scalar')
        if c == '%' and s.col() == 0: s.bad('reserved for directives')
        if c in '-?:' and (n in ('', ' ', '\t', '\n') or (flow and n in FLOWI)): s.bad('bad start of a plain scalar')
        b = s.i
        while True:
            c, n = s.ch(), s.ch(1)
            if c in ('', '\n'): break
            if c == '#' and s.t[s.i - 1] in ' \t': break
            if c == ':' and (n in ('', ' ', '\t', '\n') or (flow and n in FLOWI)): break
            if flow and c in FLOWI: break
            s.i += 1
        v = s.t[b:s.i]; w = v.rstrip(' \t')
        s.i -= len(v) - len(w)
        return w
    def double(s):
        s.i += 1; o = []
        while True:
            c = s.ch()
            if c in ('', '\n'): s.bad('unclosed quote')
            s.i += 1
            if c == '"': return ''.join(o)
            if c != '\\': o.append(c); continue
            e = s.ch(); s.i += 1
            if e == 'u':
                h = s.t[s.i:s.i + 4]
                if not re.fullmatch(r'[0-9A-Fa-f]{4}', h): s.bad('bad escape')
                s.i += 4; u = int(h, 16)
                if 0xD800 <= u < 0xDC00:
                    h2 = s.t[s.i:s.i + 6]
                    if not re.fullmatch(r'\\u[dD][c-fC-F][0-9A-Fa-f]{2}', h2): s.bad('lone surrogate')
                    s.i += 6; u = 0x10000 + ((u - 0xD800) << 10) + (int(h2[2:], 16) - 0xDC00)
                elif 0xDC00 <= u < 0xE000: s.bad('lone surrogate')
                o.append(chr(u))
            elif e and e in '"\\/bfnrt': o.append({'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t'}.get(e, e))
            else: s.bad('bad escape')
    def single(s):
        s.i += 1; o = []
        while True:
            c = s.ch()
            if c in ('', '\n'): s.bad('unclosed quote')
            s.i += 1
            if c == "'":
                if s.ch() == "'": o.append("'"); s.i += 1; continue
                return ''.join(o)
            o.append(c)
    def block(s, n):
        fold = s.ch() == '>'; s.i += 1; chomp = False
        if s.ch() == '-': chomp = True; s.i += 1
        s.eol(); lines = []; m = None
        while not s.eof():
            e = s.t.find('\n', s.i); e = len(s.t) if e < 0 else e
            line = s.t[s.i:e]
            if line.strip(' ') == '' and (m is None or len(line) <= m):
                lines.append(''); s.i = min(e + 1, len(s.t)); continue
            ind = len(line) - len(line.lstrip(' '))
            if m is None:
                if ind <= n or ind < 1: break
                m = ind
            elif ind < m: break
            lines.append(line[m:]); s.i = min(e + 1, len(s.t))
        while lines and lines[-1] == '': lines.pop()
        if not lines: return ''
        if fold:
            for l in lines:
                if l[:1] in (' ', '\t'): s.bad('more-indented line in >')
            o = ''; blanks = 0; seen = False
            for l in lines:
                if l == '': blanks += 1; continue
                if seen: o += ' ' if blanks == 0 else '\n' * blanks
                else: o += '\n' * blanks
                o += l; seen = True; blanks = 0
            v = o
        else: v = '\n'.join(lines)
        return v if chomp else v + '\n'
    def fs(s):
        j = s.i
        if s.white():
            if s.ch() == '#':
                while s.ch() not in ('\n', ''): s.i += 1
            if s.ch() == '\n': s.i += 1
            else: s.i = j
        while True:
            c = s.ch()
            if c in (' ', '\n'): s.i += 1
            elif c == '#' and (s.bol() or s.t[s.i - 1] in ' \n'):
                while s.ch() not in ('\n', ''): s.i += 1
            else: return
    def flow(s):
        s.enter(); v = s.fseq() if s.ch() == '[' else s.fmap(); s.leave(); return v
    def fnode(s):
        c = s.ch()
        if c and c in '[{': return s.flow()
        if c == '"': return s.double()
        if c == "'": return s.single()
        if c == '*': return s.ref(True)
        return s.plain(True)
    def fseq(s):
        s.i += 1; o = []; s.fs()
        while s.ch() != ']':
            if re.match(r'-<< +\*', s.t[s.i:s.i + 40]):
                if s.td is not None and s.td != 1: s.bad('merge deep in the table')
                s.i += 3; s.spaces(); src = s.ref(True)
                if not isinstance(src, list): s.bad('-<< needs a sequence')
                o += src
            else: o.append(s.fnode())
            s.fs()
            if s.ch() == ',': s.i += 1; s.fs()
            elif s.ch() != ']': s.bad('expected , or ]')
        s.i += 1; return o
    def fmap(s):
        s.i += 1; o = {}; w = set(); started = False; s.fs()
        while s.ch() != '}':
            if s.t.startswith('<<:', s.i) and s.ch(3) == ' ':
                if started: s.bad('merge after a key')
                if s.td is not None and s.td != 1: s.bad('merge deep in the table')
                s.i += 3; s.spaces(); src = s.ref(True)
                if not isinstance(src, dict): s.bad('merge needs a mapping')
                o.update(src)
            else:
                q = s.ch() in ('"', "'")
                k = s.double() if s.ch() == '"' else s.single() if q else s.plain(True)
                if not q and k == '<<': s.bad('plain << key')
                s.colon()
                if k in w: s.bad('duplicate key')
                if not q and s.ch() not in (' ', '\t', '\n', ',', '}'): s.bad('space needed after :')
                w.add(k); started = True; s.fs()
                o[k] = '' if s.ch() in (',', '}') else s.fnode()
            s.fs()
            if s.ch() == ',': s.i += 1; s.fs()
            elif s.ch() != '}': s.bad('expected , or }')
        s.i += 1; return o
    def ref(s, flow):
        if s.ch() != '*': s.bad('expected a reference')
        s.i += 1; steps = [s.step(flow)]
        while s.ch() == ':' and s.ch(1) not in ('', ' ', '\n', '\t') and not (flow and s.ch(1) in ',]}'):
            s.i += 1; steps.append(s.step(flow))
        return s.resolve(steps)
    def step(s, flow):
        if s.ch() == '<':
            e = s.t.find('>', s.i); nl = s.t.find('\n', s.i)
            if e < 0 or (0 <= nl < e) or e == s.i + 1: s.bad('bad <...>')
            k = s.t[s.i + 1:e]; s.i = e + 1
            if s.ch() not in ('', ' ', '\n', ':') and not (flow and s.ch() in ',]}'): s.bad('text after >')
            if s.ch() == ':' and s.ch(1) == ':': s.bad('colons after >')
            return k
        b = s.i
        while True:
            c = s.ch()
            if c in ('', ' ', '\t', '\n') or (flow and c in ',]}'): break
            if c == ':':
                r = 0
                while s.ch(r) == ':': r += 1
                if r == 1: break
                s.i += r; continue
            s.i += 1
        if s.i == b: s.bad('empty step')
        return s.t[b:s.i]
    def resolve(s, steps):
        if steps[0] not in s.table: s.bad(f'no entry {steps[0]}')
        v = s.table[steps[0]]
        for k in steps[1:]:
            if not isinstance(v, dict): s.bad('step through a non-mapping')
            if k not in v: s.bad(f'no key {k}')
            v = v[k]
        return v
    # plain references are banned in the table; only merges call ref directly there
    _line_node = line_node
    def line_node(s, n):
        if s.td is not None and s.ch() == '*': s.bad('reference in the table')
        return s._line_node(n)
    _fnode = fnode
    def fnode(s):
        if s.td is not None and s.ch() == '*': s.bad('reference in the table')
        return s._fnode()

def read(t):
    if not t.startswith('%YAML'): t = '%YAML 2.0\n' + t
    return P(t).stream()

spec = open(sys.argv[1], encoding='utf-8').read()
ok = bad = 0
blocks = list(re.finditer(r'```(yaml refused|yaml|json)\n(.*?)```', spec, re.S))
i = 0
while i < len(blocks):
    kind, body = blocks[i].group(1), blocks[i].group(2)
    line = spec.count('\n', 0, blocks[i].start()) + 1
    if kind == 'yaml refused':
        try:
            r = read(body); print(f'line {line}: NOT REFUSED: {body!r} -> {r.docs}'); bad += 1
        except No: ok += 1
    elif kind == 'yaml':
        want = [json.loads(l) for l in blocks[i + 1].group(2).splitlines()] if i + 1 < len(blocks) and blocks[i + 1].group(1) == 'json' else None
        i += 1
        try:
            got = [d[1] for d in read(body).docs]
            if json.dumps(got) != json.dumps(want):
                print(f'line {line}: WRONG\n  got  {json.dumps(got)}\n  want {json.dumps(want)}'); bad += 1
            else: ok += 1
        except No as e:
            print(f'line {line}: REFUSED: {e}'); bad += 1
    i += 1
print(f'spec examples: {ok} pass, {bad} fail')

D = '%YAML 2.0\n'
good = [
 ('a : 1\nlonger : 2\n', [{"a": "1", "longer": "2"}]),
 ('{"a":1,"b":[true,null]}\n', [{"a": "1", "b": ["true", "null"]}]),
 ('--- &\na: [x]\n- -<< *a\n', None),
 ('--- &\ns: [x]\n---\n- -<< *s\n  - y\n- z\n', [[["x", "y"], "z"]]),
 ('- a:\n  - x\n  b: 1\n', [[{"a": ["x"], "b": "1"}]]),
 ('- - - x\n', [[[["x"]]]]),
 ('a:\n  |\n    text\n', [{"a": "text\n"}]),
 ('a: |\n\n  x\n', [{"a": "\nx\n"}]),
 ('a: >\n\n  x\n\n\n  y\n', [{"a": "\nx\n\ny\n"}]),
 ('- |\n  x\n- y\n', [["x\n", "y"]]),
 ('a: |\n  x', [{"a": "x\n"}]),
 ('a: |\n  x\n    \n  y\n', [{"a": "x\n  \ny\n"}]),
 ('a: |\n  x\n  \n  y\n', [{"a": "x\n\ny\n"}]),
 ('a: |\nb: 1\n', [{"a": "", "b": "1"}]),
 ('---\na: 1\n...\n\n---\nb: 2\n', [{"a": "1"}, {"b": "2"}]),
 ('--- &\na: 1\n%YAML 2.0\n---\nb: *a\n', [{"b": "1"}]),
 ('--- &\na: 1\n--- &\nb: 2\n---\n[*a, *b]\n', [["1", "2"]]),
 ('--- &\na: 1\n--- &\na: 2\n---\nb: *a\n', [{"b": "2"}]),
 ('--- &\na: 1\n---\nb: *a\n--- &\na: 2\n---\nb: *a\n', [{"b": "1"}, {"b": "2"}]),
 ('--- &\na: {p: 1}\n--- &\na:\n  <<: *a\n  q: 2\n---\nb: *a\n', [{"b": {"p": "1", "q": "2"}}]),
 ('--- &\na: {p: 1}\nb:\n  <<: *a\n--- &\na: {p: 2}\n---\n[*a:p, *b:p]\n', [["2", "1"]]),
 ('--- &\na: 1\n...\n--- &\na: 2\n---\nb: *a\n', [{"b": "2"}]),
 ('--- &\na: 1\n...\n--- &\n---\nb: 2\n', [{"b": "2"}]),
 ('--- &\nFn::Sub: {x: 1}\n---\na: *Fn::Sub:x\n', [{"a": "1"}]),
 ('--- &\n"my key": {x: 1}\n---\na: *<my key>:x\nb: [*<my key>:x, 1]\n', [{"a": "1", "b": ["1", "1"]}]),
 ('a: !Ref foo\n', [{"a": "!Ref foo"}]),
 ('- %d\n- @x\n- `y`\n', [["%d", "@x", "`y`"]]),
 ('  %a: 1\n', [{"%a": "1"}]),
 ('[%a, @b]\n', [["%a", "@b"]]),
 ('a: b#c\n', [{"a": "b#c"}]),
 ('a: x:y:z\nb: http://x.y/z\n', [{"a": "x:y:z", "b": "http://x.y/z"}]),
 ('a: "\\ud83d\\ude00"\n', [{"a": "\U0001F600"}]),
 ('a: x\ty\n', [{"a": "x\ty"}]),
 ('a: foo\t\n', [{"a": "foo"}]),
 ('a: foo \t \n', [{"a": "foo"}]),
 ('a: foo\t# c\n', [{"a": "foo"}]),
 ('a: "x"\t\n', [{"a": "x"}]),
 ('a:\t\n', [{"a": ""}]),
 ('- x\t\n', [["x"]]),
 ('-\t\n', [[""]]),
 ('---\t\na: 1\n', [{"a": "1"}]),
 ('---\na: 1\n...\t\n---\nb: 2\n', [{"a": "1"}, {"b": "2"}]),
 ('[a,\t\n b\t\n]\n', [["a", "b"]]),
 ('[a,\t# c\n b]\n', [["a", "b"]]),
 ('{a:\t\n  b}\n', [{"a": "b"}]),
 ('"\\uFEFF"\n', [chr(0xfeff)]),
 ('-<<x\n', ['-<<x']),
 ('[1,\n 2,  # c\n]\n', [["1", "2"]]),
 ('a:\n  - x\n# c\n  - y\n', [{"a": ["x", "y"]}]),
 ('--- !job {a: 1}\n', [{"a": "1"}]),
 ('--- "x"\n', ["x"]),
 ('--- &\n---\n', [""]),
 ('', []),
 ('# only a comment\n', []),
]
refused = ['a:\tb\n', '-\tb\n', 'a: \tfoo\n', '[a\t, b]\n', '[a, b\t]\n', '{a:\tb}\n', 'a: 1\n\t\nb: 2\n', 'a: 1\n\t# c\nb: 2\n', '---\tfoo\n', 'a\t: 1\n', '\ta: 1\n', '"a\ufeffb"\n', '# \ufeff\n', '"a\x01b"\n', 'a: 1\n%YAML 1.2\n---\nb: 2\n', 'a: 1\n%YAML 2.1\n---\nb: 2\n', '--- &\na: 1\na: 2\n', '--- &\na: 1\n--- &\nb: 2\nb: 3\n', '--- &\na: 1\n...\n---\nb: *a\n', '--- &\na: 1\n...\n%YAML 2.0\n---\nb: *a\n', '--- &\na: {p: 1}\n...\n---\n<<: *a\n', '%a: 1\n', '---\n%foo\n', '[\n%a\n]\n', 'a: >\n  x\n     \n  y\n', 'a: -<< *s\n', '{a: -<< *s}\n', 'key:\tvalue\n', '\tkey: v\n', '--- & x\n', '--- !\na: 1\n', '--- ! x\n',
 "a: 'x' y\n", 'a: [1] b\n', '--- foo: bar\n', '--- - x\n', '--- &\na: 1\n---\nb: *a c\n', '--- &\na: 1\n---\nb: *<a>x\n',
 '--- &\na: 1\n---\nb: *<>\n', '--- &\na: 1\n---\nb: *a:\n', 'a: 1\na: 2\n', '<< : x\n', '<<:\n',
 'a: |0\n  x\n', 'a: |-2\n  x\n', 'a: >+\n  x\n', '--- &\n<<: *a\n', '--- &\na: 1\nb:\n  - *a\n', '--- &\ns: [x]\nt:\n  u:\n    -<< *s\n',
 '--- &\na: {p: 1}\nb: {c: {<<: *a}}\n', 'a: "\\ud83d"\n', 'a: "x\n', "a: 'x\n", 'a: *nope\n', '[1, 2\n---\n', '{a: 1, a: 2}\n', '{"a": 1 "b": 2}\n', '[,]\n', '{,}\n', ': x\n', '- x\ny: 1\n', 'a: 1\n- x\n', 'a: 1\n  b: 2\n']
f = 0
for t, want in good:
    if want is None: continue
    try:
        got = [d[1] for d in read(t).docs]
        if json.dumps(got) != json.dumps(want): print('WRONG', repr(t), got, want); f += 1
    except No as e: print('REFUSED', repr(t), e); f += 1
for t in refused:
    try:
        r = read(t); print('NOT REFUSED', repr(t), [d[1] for d in r.docs]); f += 1
    except No: pass
for t in ('a: 1\n', '%YAML 1.2\na: 1\n', '# c\n%YAML 2.0\n', '\ufeff%YAML 2.0\n'):
    try: P(t).stream(); print('NOT REFUSED', repr(t)); f += 1
    except No: pass
r = read('---\nt: 1\n...\n# H\n'); assert r.stopped == len('%YAML 2.0\n---\nt: 1\n...\n'), r.stopped
print(f'edge cases: {len(good) + len(refused) + 4 - sum(1 for g in good if g[1] is None)} run, {f} fail')
