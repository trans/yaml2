"""Test spec/yaml-2.0.md: a throwaway parser written from its grammar. Not a reference.

    python3 -I draftcheck.py SPEC SUITE

Runs every example in the draft, then every test in the suite's src directory (it needs
PyYAML for that), then checks the size limit's internal counts. Every example must be in the
suite, tagged spec, with the same result, and every test tagged spec must be in the draft.
Exits with 1 if anything fails. The size limit is counted after each
document and table entry, both held and full, and is off by default. With keep=True a
reference stays a reference, so `-<<` adds its size and builds nothing, and data read that
way has to pass expand() first. Python integers don't wrap, so the count that stops at its
largest value is shown in size_tests by working it out at a fixed width.
"""
import json, os, re, sys
class No(Exception): pass
FLOWI = ',[]{}'
sys.setrecursionlimit(20000)
IND = ",[]{}#&*|>'\""
NAME = re.compile('[A-Za-z0-9._/\\-\u00b7\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u037d\u037f-\u1fff\u200c-\u200d\u203f-\u2040\u2070-\u218f\u2c00-\u2fef\u3001-\ud7ff\uf900-\ufdcf\ufdf0-\ufefe\uff00-\ufffd\U00010000-\U000effff]')
def put(d, k, v):
    """A key replaced by a later one keeps its place, and takes the later one's spelling (part 2, section 7)."""
    if k in d:
        items = [(k if j == k else j, w) for j, w in d.items()]; d.clear(); d.update(items)
    d[k] = v
class L(list):
    """A sequence that keeps references: `-<<` adds to more and deep, and no items."""
    more = 0; deep = 0
class P:
    def __init__(s, t, limit=None, together=False, keep=False, maxlevels=None):
        s.dq = []; s.limit = limit; s.together = together; s.memo = {}; s.tsize = {}; s.sizes = []; s.keep = keep; s.theld = 0; s.saved = 0; s.helds = []
        s.dheld = s.dfull = 0; s.maxlevels = maxlevels; s.lmemo = {}
        s.raw = t; s.t = t.replace('\r\n', '\n'); s.i = 0; s.table = {}; s.docs = []; s.stopped = None; s.intable = False
    def nsize(s, v):
        """A node's size. A shared object counts in full at every use."""
        if isinstance(v, str): return 1 + len(v.encode('utf-8', 'surrogatepass'))
        m = s.memo.get(id(v))
        if m is None:
            m = (v, 1 + (sum(s.nsize(x) for x in v) + getattr(v, 'more', 0) if isinstance(v, list) else sum(s.nsize(k) + s.nsize(x) for k, x in v.items())))
            s.memo[id(v)] = m
        return m[1]
    def levels(s, v):
        """Levels with references followed. Each collection is one, and strings none."""
        if isinstance(v, str): return 0
        m = s.lmemo.get(id(v))
        if m is None:
            kids = v if isinstance(v, list) else v.values()
            m = max(1 + max((s.levels(x) for x in kids), default=0), getattr(v, 'deep', 0))
            s.lmemo[id(v)] = m
        return m
    def deep(s, v):
        if s.maxlevels is not None and s.levels(v) > s.maxlevels: s.bad('too deep')
    def expand(s, v):
        """What expanding kept references checks first."""
        s.check(min(s.nsize(v), 2 ** 64 - 1)); s.deep(v)
    def check(s, n):
        if s.limit is not None and n > s.limit: s.bad('past the size limit')
    def entry(s, k, v):
        s.tsize[k] = s.nsize(k) + s.nsize(v)
        s.theld += s.tsize[k] - s.saved; s.saved = 0
        s.tally(0, 0)
        if not s.keep: s.deep(v)
    def tally(s, h, n):
        s.check(s.theld + (s.dheld if s.together else h))
        if not s.keep: s.check(sum(s.tsize.values()) + (s.dfull if s.together else n))
    def plainref(s, flow):
        v = s.ref(flow); s.saved += s.nsize(v) - 1
        return v
    def splice(s, out, src):
        s.saved += s.nsize(src) - 2
        if s.keep:
            out.more += s.nsize(src) - 1; out.deep = max(out.deep, s.levels(src))
        else:
            s.check(s.nsize(src)); out += src
    def deliver(s, name, v):
        n = s.nsize(v) + (s.nsize(name) if name else 0)
        h = n - s.saved; s.saved = 0
        s.sizes.append((sum(s.tsize.values()), n)); s.helds.append((s.theld, h))
        s.dheld += h; s.dfull += n
        s.tally(h, n)
        if not s.keep: s.deep(v)
        s.docs.append((name, v))
    def offset(s):
        """Section 4.4's offset of the line after a stopping `...`: bytes of the stream as written."""
        if s.stopped is None: return None
        n = s.t.count('\n', 0, s.stopped); i = 0
        for _ in range(n): i = s.raw.index('\n', i) + 1
        return len(s.raw[:i].encode('utf-8', 'surrogatepass'))
    def finish(s):
        """Characters, over what was read: nothing after a final `...` counts."""
        t = s.t if s.stopped is None else s.t[:s.stopped]
        if '\r' in t: raise No('lone CR')
        if re.search('[\x00-\x08\x0b\x0c\x0e-\x1f]', t): raise No('character not allowed')
        last = 0; out = []
        for a, b in sorted(set(s.dq)):
            if a < last or b > len(t): continue
            out.append(t[last:a]); last = b
        out.append(t[last:])
        if re.search('[^\t\n\x20-\x7e\xa0-\u2027\u202a-\ud7ff\ue000-\ufefe\uff00-\ufffd\U00010000-\U0010ffff]', ''.join(out)): raise No('character not allowed')
        return s
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
        while True:
            s.gap()
            if s.eof(): return s
            ended = s.dots()
            if ended:
                s.i += 3; s.eol(); after = s.i
                while True:
                    j = s.i; s.spaces()
                    if s.ch() == '\n': s.i += 1
                    else: s.i = j; break
                if s.eof(): return s
                if not s.marker() and not s.directive_then_marker():
                    s.stopped = after; return s
                if s.keep and s.together: s.dheld += s.theld
                s.table = {}; s.tsize = {}; s.theld = 0
            if s.directive_then_marker():
                if not ended: s.bad('%YAML 2.0 can only come again after ...')
                s.i += 9; s.eol(); s.gap()
            if not s.marker(): s.bad('expected a marker')
            s.document()
    def document(s):
        s.i += 3; j = s.i; n = s.spaces(); s.intable = False
        if n and s.ch() == '&':
            s.i += 1; k = s.i; s.intable = True
            if s.spaces() and s.ch() == '{':
                s.tableflow(); s.eol(); s.gap(); return
            s.i = k; s.eol(); s.gap(); k = s.i; s.spaces()
            if s.ch() == '{':
                s.tableflow(); s.eol(); s.gap(); return
            s.i = k; s.tablemap(); return
        name = None
        if n and s.ch() == '!':
            s.i += 1; b = s.i
            while NAME.match(s.ch() or ' '): s.i += 1
            name = s.t[b:s.i]
            if not name: s.bad('no name')
            j = s.i; n = s.spaces()
        if n and s.ch() not in ('#', '\n', ''):
            s.deliver(name, s.line_node(0))
        else:
            s.i = j; s.eol(); s.gap(); s.deliver(name, s.node(-1, top=True))
    def tableflow(s):
        here = set(); s.i += 1; s.fs()
        while s.ch() != '}':
            if s.t.startswith('<<:', s.i): s.bad('merge outside an entry')
            q = s.ch() in ('"', "'")
            k = s.double() if s.ch() == '"' else s.single() if q else s.plain(True)
            if not q and k == '<<': s.bad('plain << key')
            s.fs() if q else s.white()
            s.colon()
            if k in here: s.bad('key repeated in one table document')
            here.add(k)
            if not q and s.ch() not in (' ', '\t', '\n', ',', '}'): s.bad('space needed after :')
            s.fs()
            s.table[k] = '' if s.ch() in (',', '}') else s.fnode()
            s.entry(k, s.table[k])
            s.fs()
            if s.ch() == ',': s.i += 1; s.fs()
            elif s.ch() != '}': s.bad('expected , or }')
        s.i += 1
    def tablemap(s):
        here = set()
        while True:
            s.gap()
            if s.eof() or s.marker() or s.dots() or s.ch() == '%': break
            if s.ch() == ' ': s.bad('table entries are at column 0')
            if s.t.startswith('<<:', s.i): s.bad('merge outside an entry')
            k = s.key(); s.colon()
            if k in here: s.bad('key repeated in one table document')
            here.add(k); s.tsize.pop(k, None)
            s.table[k] = s.value(0, True)
            s.entry(k, s.table[k])
            s.gap()
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
    def enter(s): pass
    def leave(s): pass
    def counted(s, v, x):
        """A mapping's size counts the merged pairs later lines replaced (x), wherever it is named."""
        s.memo.pop(id(v), None); s.memo[id(v)] = (v, s.nsize(v) + x); return v
    def map(s, m):
        s.enter(); out = {}; written = set(); started = False; x = 0
        while True:
            j = s.i
            if not s.at(m): s.i = j; break
            if s.t.startswith('<<:', s.i) and s.ch(3) in (' ', '\n', ''):
                if started: s.bad('merge after a key')
                s.i += 3
                if not s.spaces(): s.bad('merge needs a reference')
                src = s.ref(False); s.eol()
                if not isinstance(src, dict): s.bad('merge needs a mapping')
                s.saved += s.nsize(src) - 2
                for k, v in src.items():
                    if k in out: x += s.nsize(k) + s.nsize(out[k])
                    put(out, k, v)
            else:
                if not s.is_map(): s.bad('expected a key')
                k = s.key(); s.colon()
                if k in written: s.bad('duplicate key')
                written.add(k); started = True
                if k in out: x += s.nsize(k) + s.nsize(out[k])
                put(out, k, s.value(m, True))
            s.gap()
        s.leave(); return s.counted(out, x)
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
        s.enter(); out = L()
        while True:
            j = s.i
            if not s.at(m): s.i = j; break
            if not s.is_seq(): s.i = j; break
            if s.ch(1) == '<':
                s.i += 3; s.spaces(); src = s.ref(False); s.eol()
                if not isinstance(src, list): s.bad('-<< needs a sequence')
                s.splice(out, src)
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
        elif c == '*': v = s.plainref(False)
        elif c == '"': v = s.double()
        elif c == "'": v = s.single()
        else: v = s.plain(False)
        s.eol(); return v
    def plain(s, flow):
        c, n = s.ch(), s.ch(1)
        if re.match(r'-<<[ \t]+\*', s.t[s.i:s.i + 40]): s.bad('-<< outside a sequence')
        if not c or c in IND or c in ' \t\n': s.bad('bad start of a plain scalar')
        if c == '%' and s.col() == 0: s.bad('reserved for directives')
        if c == '!' and not s.intable: s.bad('! starts a plain scalar outside the table')
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
        b = s.i; s.i += 1; o = []
        while True:
            c = s.ch()
            if c in ('', '\n'): s.bad('unclosed quote')
            s.i += 1
            if c == '"': s.dq.append((b, s.i)); return ''.join(o)
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
        s.eol(); lines = []; m = None; wide = 0
        while not s.eof():
            e = s.t.find('\n', s.i); e = len(s.t) if e < 0 else e
            line = s.t[s.i:e]
            if line.strip(' ') == '' and (m is None or len(line) <= m):
                if m is None: wide = max(wide, len(line))
                lines.append(''); s.i = min(e + 1, len(s.t)); continue
            ind = len(line) - len(line.lstrip(' '))
            if m is None:
                if ind <= n or ind < 1: break
                m = ind
                if wide > m: s.bad('a leading blank line wider than the text')
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
        while True:
            c = s.ch()
            if s.bol() and (s.marker() or s.dots()): s.bad('marker inside a flow collection')
            if c in (' ', '\t', '\n') and c: s.i += 1
            elif c == '#' and (s.bol() or s.t[s.i - 1] in ' \t\n'):
                while s.ch() not in ('\n', ''): s.i += 1
            else: return
    def flow(s):
        s.enter(); v = s.fseq() if s.ch() == '[' else s.fmap(); s.leave(); return v
    def fnode(s):
        c = s.ch()
        if c and c in '[{': return s.flow()
        if c == '"': return s.double()
        if c == "'": return s.single()
        if c == '*': return s.plainref(True)
        return s.plain(True)
    def fseq(s):
        s.i += 1; o = L(); s.fs()
        while s.ch() != ']':
            if s.t.startswith('-<<', s.i) and s.ch(3) in (' ', '\t', '\n'):
                j = s.i; s.i += 3; s.fs()
                if s.ch() == '*':
                    src = s.ref(True)
                    if not isinstance(src, list): s.bad('-<< needs a sequence')
                    s.splice(o, src)
                else: s.i = j; o.append(s.fnode())
            else: o.append(s.fnode())
            s.fs()
            if s.ch() == ',': s.i += 1; s.fs()
            elif s.ch() != ']': s.bad('expected , or ]')
        s.i += 1; return o
    def fmap(s):
        s.i += 1; o = {}; w = set(); started = False; x = 0; s.fs()
        while s.ch() != '}':
            if s.t.startswith('<<:', s.i) and s.ch(3) in (' ', '\t', '\n'):
                if started: s.bad('merge after a key')
                s.i += 3; s.fs(); src = s.ref(True)
                if not isinstance(src, dict): s.bad('merge needs a mapping')
                s.saved += s.nsize(src) - 2
                for k, v in src.items():
                    if k in o: x += s.nsize(k) + s.nsize(o[k])
                    put(o, k, v)
            else:
                q = s.ch() in ('"', "'")
                k = s.double() if s.ch() == '"' else s.single() if q else s.plain(True)
                if not q and k == '<<': s.bad('plain << key')
                s.fs() if q else s.white()
                s.colon()
                if k in w: s.bad('duplicate key')
                if not q and s.ch() not in (' ', '\t', '\n', ',', '}'): s.bad('space needed after :')
                w.add(k); started = True; s.fs()
                if k in o: x += s.nsize(k) + s.nsize(o[k])
                put(o, k, '' if s.ch() in (',', '}') else s.fnode())
            s.fs()
            if s.ch() == ',': s.i += 1; s.fs()
            elif s.ch() != '}': s.bad('expected , or }')
        s.i += 1; return s.counted(o, x)
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
            if s.ch() not in ('', ' ', '\t', '\n', ':') and not (flow and s.ch() in ',]}'): s.bad('text after >')
            if s.ch() == ':' and s.ch(1) == ':': s.bad('colons after >')
            return k
        b = s.i
        while True:
            c = s.ch()
            if c in ('', ' ', '\t', '\n') or (flow and c in ',]}'): break
            if c == '>': s.bad('> in a path')
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

def framed(t):
    """Add what the examples leave out: %YAML 2.0, and a plain --- if no marker comes first."""
    if t.startswith('%YAML'): return t
    body = re.sub(r'\A(?:[ \t]*(?:#[^\n]*)?\n)*', '', t)
    return '%YAML 2.0\n' + ('' if not body or body.startswith(('---', '...')) else '---\n') + t
def read(t, limit=None, together=False, keep=False, maxlevels=None):
    t = framed(t)
    return P(t, limit, together, keep, maxlevels).stream().finish()

spec = open(sys.argv[1], encoding='utf-8').read()
ok = bad = 0
examples = []
blocks = list(re.finditer(r'```(yaml refused|yaml|json)\n(.*?)```', spec, re.S))
i = 0
while i < len(blocks):
    kind, body = blocks[i].group(1), blocks[i].group(2)
    line = spec.count('\n', 0, blocks[i].start()) + 1
    if kind == 'yaml refused':
        examples.append((framed(body), None))
        try:
            r = read(body); print(f'line {line}: NOT REFUSED: {body!r} -> {r.docs}'); bad += 1
        except No: ok += 1
    elif kind == 'yaml':
        want = [json.loads(l) for l in blocks[i + 1].group(2).splitlines()] if i + 1 < len(blocks) and blocks[i + 1].group(1) == 'json' else None
        i += 1
        examples.append((framed(body), want))
        try:
            got = [d[1] for d in read(body).docs]
            if json.dumps(got) != json.dumps(want):
                print(f'line {line}: WRONG\n  got  {json.dumps(got)}\n  want {json.dumps(want)}'); bad += 1
            else: ok += 1
        except No as e:
            print(f'line {line}: REFUSED: {e}'); bad += 1
    i += 1
print(f'spec examples: {ok} pass, {bad} fail')

DEFAULT = 64 * 2 ** 20
MARKS = '␣»—←⇔↵∎'
ESCAPED = re.compile('[\x00-\x1f\x7f-\x9f\u00a0\u00ad\u1680\u180e\u2000-\u200f\u2028-\u202f\u205f-\u206f\u3000\ufeff\ufff9-\ufffb\ufffe\uffff' + MARKS + ']')
NAMED = {'\\': '\\\\', '\0': '\\0', '\b': '\\b', '\t': '\\t', '\n': '\\n', '\r': '\\r'}
def unescape(t):
    """The suite's visible characters: suite/README.md."""
    t = t.replace(MARKS[0], ' '); t = re.sub(MARKS[2] + '*' + MARKS[1], '\t', t)
    t = t.replace(MARKS[3], '\r').replace(MARKS[4], '\ufeff').replace(MARKS[5], '')
    return re.sub(MARKS[6] + '\n\\Z', '', t)
def esc(v):
    return ''.join(NAMED.get(c) or (f'\\u{ord(c):04X}' if ESCAPED.match(c) else c) for c in v)
def events(docs):
    """The suite's event notation, without indentation."""
    out = ['+STR']
    def node(v):
        if isinstance(v, str): out.append('=VAL :' + esc(v))
        elif isinstance(v, list): out.append('+SEQ'); [node(x) for x in v]; out.append('-SEQ')
        else:
            out.append('+MAP')
            for k, x in v.items(): node(k); node(x)
            out.append('-MAP')
    for name, v in docs:
        out.append('+DOC' + (' !' + esc(name) if name else '')); node(v); out.append('-DOC')
    return '\n'.join(out + ['-STR']) + '\n'
def ordered(v):
    """JSON that compares keys in order."""
    return json.dumps(json.loads(json.dumps(v), object_pairs_hook=lambda p: p))
def suite(path):
    """(file, test) for each test, with what a subtest leaves out taken from the one before."""
    import yaml
    for f in sorted(os.listdir(path)):
        if not f.endswith('.yaml'): continue
        cache = {}
        for t in yaml.safe_load(open(os.path.join(path, f), encoding='utf-8')):
            for k in ('name', 'from', 'tags', 'yaml', 'tree', 'json', 'rest'):
                if k not in t and k in cache: t[k] = cache[k]
            cache = dict(t)
            yield f, t
tests = list(suite(sys.argv[2]))
tagged = {}
for f, t in tests:
    if 'spec' in t['tags'].split():
        assert unescape(t['yaml']) not in tagged, f
        tagged[unescape(t['yaml'])] = (f, t)
for text, want in examples:
    f, t = tagged.pop(text, (None, None))
    if t is None: print('NOT IN THE SUITE', repr(text)); bad += 1
    elif bool(t.get('fail')) != (want is None) or want is not None and [ordered(json.loads(l)) for l in unescape(t['json']).splitlines()] != [ordered(w) for w in want]:
        print(f, 'NOT AS IN THE DRAFT', t['name']); bad += 1
for f, t in tagged.values(): print(f, 'NOT IN THE DRAFT', t['name']); bad += 1
f = 0
for file, t in tests:
    text = unescape(t['yaml'])
    try: r = P(text, t.get('limit', DEFAULT), t.get('together', False), t.get('keep', False)).stream().finish()
    except No as e:
        if not t.get('fail'): print(file, 'REFUSED', t['name'], e); f += 1
        continue
    if t.get('fail'): print(file, 'NOT REFUSED', t['name']); f += 1; continue
    if t.get('keep'): continue
    if 'tree' not in t or 'json' not in t: print(file, 'NO TREE OR JSON', t['name']); f += 1; continue
    if events(r.docs) != re.sub('^[ \t]+', '', unescape(t['tree']), flags=re.M):
        print(file, 'TREE', t['name']); f += 1
    if [ordered(json.loads(l)) for l in unescape(t['json']).splitlines()] != [ordered(d[1]) for d in r.docs]:
        print(file, 'JSON', t['name']); f += 1
    # The offset counts bytes of the stream as written (section 4.4): the rest is what follows it.
    rest = None if r.offset() is None else text.encode('utf-8', 'surrogatepass')[r.offset():].decode('utf-8', 'surrogatepass')
    want = None if 'rest' not in t else unescape(t['rest'])
    if rest != want: print(file, 'REST', t['name'], repr(rest), repr(want)); f += 1
def size_tests():
    ex = '--- &\na: [x, yy]\nm: {k: v}\n---\nb: *a\nc:\n  -<< *a\n  - z\nd:\n  <<: *m\n'
    assert read(ex).sizes == [(15, 26)], read(ex).sizes
    assert read(ex).helds == [(15, 14)], read(ex).helds
    read(ex, 41)
    def no(*a):
        try: read(*a)
        except No: return
        raise AssertionError(a)
    no(ex, 40)
    read(ex, 29, False, True)
    try: read(ex, 28, False, True); raise AssertionError('held')
    except No: pass
    r = read('--- &\nm: {k: v}\n---\nc:\n  <<: *m\n  k: w\n')
    assert r.sizes == [(7, 12)] and r.helds == [(7, 9)], (r.sizes, r.helds)
    big = '--- &\nbig: [' + ', '.join(['x'] * 1000) + ']\n' + '---\na: *big\n' * 100
    r = read(big); assert r.sizes[0] == (2005, 2004) and r.helds[0] == (2005, 4), (r.sizes[0], r.helds[0])
    read(big, 4009); no(big, 4008); no(big, 4009, True)
    read(big, 2009, False, True); no(big, 2008, False, True); read(big, 2405, True, True); no(big, 2404, True, True)
    plain = '[' + 'x, ' * 1000 + ']\n'
    read(plain, 2001); no(plain, 2000); read(plain, 2001, False, True); no(plain, 2000, False, True)
    st = '---\na: 1\n---\nb: 2\n---\nc: 3\n'
    m = max(n for _, n in read(st).sizes); read(st, m); no(st, m, True); read(st, 3 * m, True)
    assert read('--- &\nm: {k: v}\n---\nc:\n  <<: *m\n  k: w\n').sizes[0][1] == 12
    assert read('--- &\na: x\n--- &\na: yyy\n---\nb: 1\n').sizes[0][0] == 6
    assert read('--- &\na: x\n...\n---\nb: 1\n').sizes[0][0] == 0
    dbl = '--- &\na: [x, x]\n' + ''.join(f'a{i}:\n  -<< *{"a" if i == 0 else "a" + str(i - 1)}\n  -<< *{"a" if i == 0 else "a" + str(i - 1)}\n' for i in range(40))
    no(dbl, 100000)
    ref = '--- &\na: [x, x]\n' + ''.join(f'a{i}: [*{"a" if i == 0 else "a" + str(i - 1)}, *{"a" if i == 0 else "a" + str(i - 1)}]\n' for i in range(40))
    no(ref, 100000); read(ref, 100000, False, True)
    assert read('[' * 256 + ']' * 256 + '\n').docs
    assert read(''.join(' ' * i + 'k:\n' for i in range(256)) + ' ' * 256 + 'v\n').docs
    rep = '--- &\na: [x, yy]\n--- &\na: [z]\n---\nb: *a\n'
    r = read(rep); assert r.sizes == [(5, 6)] and r.helds == [(13, 4)], (r.sizes, r.helds)
    read(rep, 17); no(rep, 16); read(rep, 17, False, True); no(rep, 16, False, True)
    one = lambda i: f'--- &\ne: {"x" * 990}{i:04d}\n---\nv: *e\n'
    many = ''.join(one(i) for i in range(200)); cut = 64 * 997
    for kw in ((False, False), (False, True), (True, False), (True, True)): no(many, cut, *kw)
    wrote = ''.join('...\n' * (i > 0) + one(i) for i in range(200))
    read(wrote, cut); read(wrote, cut, False, True)
    read(wrote, 200 * 997 + 800, True, True); no(wrote, 200 * 997 + 799, True, True)
    no(wrote, cut, True, False)
    log = '--- &\nlog: []\n' + '--- &\nlog:\n  -<< *log\n  - a\n---\nn: *log\n' * 1000
    assert read(log).helds[-1][0] == 5 + 8 * 1000 - 0, read(log).helds[-1]
    read(log, 12000); read(log, 8010, False, True)
    chain = '--- &\na0: [x, x]\n' + ''.join(f'a{i}:\n  -<< *a{i - 1}\n  -<< *a{i - 1}\n' for i in range(1, 63)) + '---\nb: *a62\n'
    lim = 64 * 2 ** 20; no(chain, lim)
    r = read(chain, lim, False, True); v = r.docs[-1][1]['b']
    assert r.nsize(v) == 2 ** 64 + 1 and sum(r.helds[-1]) < 2000, (r.nsize(v), r.helds)
    w = 5
    for _ in range(62): w = ((w - 1) * 2 + 1) % 2 ** 64
    assert w == 1 and w <= lim
    w = 5
    for _ in range(62): w = min((w - 1) * 2 + 1, 2 ** 64 - 1)
    assert w == 2 ** 64 - 1 and w > lim
    try: r.expand(v); raise AssertionError('expand')
    except No: pass
    deep = lambda n: '--- &\ne0: x\n' + ''.join(f'e{i}: [*e{i - 1}]\n' for i in range(1, n + 1)) + f'---\ny: *e{n}\n'
    r = read(deep(999)); assert r.levels(r.docs[-1][1]) == 1000
    read(deep(255), None, False, False, 256)
    try: read(deep(256), None, False, False, 256); raise AssertionError('levels')
    except No: pass
    r = read(deep(256), None, False, True, 256)
    try: r.expand(r.docs[-1][1]); raise AssertionError('levels kept')
    except No: pass
    named = '--- !' + 'n' * 100000 + '\na: 1\n'
    no(named, 100); read(named, 100006); no(named, 100005); no(named, 100005, False, True)
    r = read('--- !abc\na: 1\n'); assert r.sizes == [(0, 9)] and r.helds == [(0, 9)], (r.sizes, r.helds)
    names = ''.join('--- !' + 'n' * 1000 + f'\na{i:03d}: 1\n' for i in range(1000))
    no(names, 10000, True); read(names, 1000 * 1009, True); no(names, 1000 * 1009 - 1, True); read(names, 1009); no(names, 1008)
    swap = '--- &\na: [x, yy]\n--- &\na:\n  -<< *a\n  - z\n---\nb: 1\n'
    r = read(swap); assert r.sizes == [(10, 5)] and r.helds == [(14, 5)], (r.sizes, r.helds)
    assert read('--- &\na: [x, yy]\n--- &\na:\n  -<< *a\n  - z\n').tsize['a'] == 10
    read(swap, 19); no(swap, 18); read(swap, 19, False, True); no(swap, 18, False, True)
    peak = '--- &\na: [x, yy]\n--- &\na:\n  -<< *a\n  - z\n'
    read(peak, 14); no(peak, 13); read(peak, 14, False, True)
    esc = '---\n"\\u00e9": "\\u00e9"\n'
    r = read(esc); assert r.sizes == [(0, 7)] and r.helds == [(0, 7)], (r.sizes, r.helds)
    spl = '--- &\ns: [[[x]]]\n---\n- -<< *s\n- y\n'
    r = read(spl, None, False, True); assert r.levels(r.docs[-1][1]) == 4, r.levels(r.docs[-1][1])
    assert read(spl).levels(read(spl).docs[-1][1]) == 4
size_tests()
print(f'suite: {len(tests)} tests, {f} fail')
sys.exit(1 if bad or f else 0)
