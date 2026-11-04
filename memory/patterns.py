"""Sort real patterns by the simplest notation that could write them.

    python3 -I patterns.py DIR

DIR holds JSON Schemas: SchemaStore's src/schemas/json is what the notes cite.
Reads `pattern` values and `patternProperties` keys. Each unique pattern goes in
the lowest tier that can write it, using Python's own regex parser, so a few
.NET and ECMAScript forms land in "not parsed".
"""
import collections, json, os, re, sys
import re._parser as P
import re._constants as C

ALL = frozenset(range(128))
CAT = {C.CATEGORY_DIGIT: r'\d', C.CATEGORY_NOT_DIGIT: r'\D', C.CATEGORY_SPACE: r'\s',
       C.CATEGORY_NOT_SPACE: r'\S', C.CATEGORY_WORD: r'\w', C.CATEGORY_NOT_WORD: r'\W'}
def cat(c):
    r = re.compile(CAT[c], re.A)
    return frozenset(i for i in ALL if r.match(chr(i)))
def chars(tok):
    op, av = tok
    if op is C.LITERAL: return frozenset([av]) & ALL or frozenset([av])
    if op is C.NOT_LITERAL: return ALL - {av}
    if op is C.ANY: return ALL
    if op is C.IN:
        s, neg = set(), False
        for o, a in av:
            if o is C.NEGATE: neg = True
            elif o is C.LITERAL: s.add(a)
            elif o is C.RANGE: s |= set(range(a[0], a[1] + 1))
            elif o is C.CATEGORY: s |= cat(a)
        return frozenset(ALL - s if neg else s)
    return None

class No(Exception): pass
LIMIT = 8      # a union past this is reported on its own; the number is a choice

def seq(items):
    """Return a list of flat sequences; each element is (chars, lo, hi)."""
    out = [[]]
    for tok in items:
        alts = elem(tok)
        out = [a + b for a in out for b in alts]
        if len(out) > 64: raise No('huge')
    return out

def single(s):
    return len(s) == 1 and s[0][1] == 1 and s[0][2] == 1

def elem(tok):
    op, av = tok
    if op is C.AT: return [[]]
    c = chars(tok)
    if c is not None: return [[(c, 1, 1)]]
    if op is C.SUBPATTERN:
        return seq(av[3])
    if op is C.BRANCH:
        alts = [s for b in av[1] for s in seq(b)]
        if alts and all(single(s) for s in alts):
            return [[(frozenset().union(*[s[0][0] for s in alts]), 1, 1)]]
        return alts
    if op in (C.MAX_REPEAT, C.MIN_REPEAT):
        lo, hi, sub = av
        ss = seq(sub)
        if len(ss) == 1 and single(ss[0]):
            return [[(ss[0][0][0], lo, hi)]]
        if hi == 1:
            return ss + [[]] if lo == 0 else ss
        raise No('repeat')
    if op in (C.ASSERT, C.ASSERT_NOT): raise No('look')
    if op is C.GROUPREF: raise No('backref')
    raise No('other')

D, UP, LOW = frozenset(range(48, 58)), frozenset(range(65, 91)), frozenset(range(97, 123))
PIC = {D, UP, LOW, UP | LOW, UP | LOW | D, ALL}

def anch(items):
    items = list(items)
    def first(l):
        while l and l[0][0] is C.SUBPATTERN: l = list(l[0][1][3])
        return l[0] if l else None
    def last(l):
        while l and l[-1][0] is C.SUBPATTERN: l = list(l[-1][1][3])
        return l[-1] if l else None
    a, b = first(items), last(items)
    return bool(a and a[0] is C.AT), bool(b and b[0] is C.AT)

def pair(c):
    return len(c) == 2 and len({chr(i).lower() for i in c}) == 1

def tier(p):
    try:
        t = P.parse(p)
    except Exception:
        return 'H', None
    try:
        ss = seq(t)
    except No as e:
        return {'repeat': 'F', 'look': 'G', 'backref': 'G'}.get(str(e), 'I'), str(e)
    l, r = anch(t)
    if not l: ss = [[(ALL, 0, 1 << 30)] + s for s in ss]
    if not r: ss = [s + [(ALL, 0, 1 << 30)] for s in ss]
    lit = lambda e: len(e[0]) == 1 and e[1] == e[2] == 1
    if all(all(lit(e) for e in s) for s in ss): return 'A', None
    if all(all(lit(e) or (pair(e[0]) and e[1] == e[2] == 1) for e in s) for s in ss):
        return 'A2', None
    if len(ss) > LIMIT: return 'E2', None
    glob = lambda e: lit(e) or (e[0] == ALL and ((e[1], e[2]) == (1, 1) or e[1] == 0 and e[2] > 1 << 20))
    if len(ss) == 1:
        s = ss[0]
        if all(glob(e) for e in s): return 'B', None
        if all(lit(e) or (e[1] == e[2] and e[0] in PIC) for e in s): return 'C', None
        if all(lit(e) or e[1] == e[2] for e in s): return 'C2', None
        return 'D', None
    return 'E', None

NAME = {'A': 'literal or enum: no pattern needed',
        'A2': 'enum with case spelled out, [Aa][Ll][Ll]', 'B': 'glob: literals, * and ?',
        'C': 'PIC: fixed shape of digit, letter, any', 'C2': 'fixed shape, needs own class (hex)',
        'D': 'flat: one sequence of class + count', 'E': 'union of up to 8 flat sequences',
        'E2': 'union of more than 8', 'F': 'repeated group', 'G': 'lookaround or backreference',
        'H': 'not parsed by Python re', 'I': 'other'}

def walk(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == 'pattern' and isinstance(v, str):
                out.append(v)
            elif k == 'patternProperties' and isinstance(v, dict):
                out.extend(x for x in v if isinstance(x, str))
            walk(v, out)
    elif isinstance(node, list):
        for v in node:
            walk(v, out)


def main(root):
    found, files = [], 0
    for f in sorted(os.listdir(root)):
        out = []
        walk(json.load(open(os.path.join(root, f), encoding='utf-8')), out)
        found += out
        files += bool(out)
    uses = collections.Counter(found)
    count = collections.Counter(tier(p)[0] for p in uses)
    need = len(uses) - count['A'] - count['A2']
    print(f'{files} schemas with patterns, {len(found)} uses, {len(uses)} unique, {need} need a pattern')
    run = 0
    for k in ('A', 'A2', 'B', 'C', 'C2', 'D', 'E', 'E2', 'F', 'G', 'H', 'I'):
        run += count[k] if k not in ('A', 'A2') else 0
        cum = '' if k in ('A', 'A2') else f'{100 * run / need:5.1f}%'
        print(f'{count[k]:6} {cum:>6}  {NAME[k]}')
    print(r'\d \w \s:', sum(bool(re.search(r'(?<!\\)\\[dwsDWS]', p)) for p in uses),
          ' not anchored at both ends:', sum(not (p.startswith('^') and p.endswith('$')) for p in uses))


if __name__ == '__main__':
    main(sys.argv[1])
