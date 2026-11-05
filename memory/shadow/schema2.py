"""JSON as an ordinary schema: a recursive named type, read by the real grammar.

    python3 -I schema2.py SCHEMASTORE_DIR JSONTESTSUITE_TEST_PARSING_DIR

One rule differs from shadow.py: a union may hold several scalar types, tried in the order
written, and a quoted scalar matches string types only.
"""
import collections, importlib.util, json, os, re, sys
Y = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
src = open(Y + 'draftcheck.py', encoding='utf-8').read().split("\nspec = open(sys.argv[1]")[0]
g = {'__name__': 'dc'}; exec(compile(src, 'dc', 'exec'), g)
P, No, read = g['P'], g['No'], g['read']
sys.setrecursionlimit(20000)
class Plain(str): pass
orig = P.plain
P.plain = lambda s, flow: Plain(orig(s, flow))
sys.dont_write_bytecode = True
sp = importlib.util.spec_from_file_location('shadow', Y + 'shadow/shadow.py')
sh = importlib.util.module_from_spec(sp); sp.loader.exec_module(sh)

class Schema2(sh.Schema):
    def __init__(self, text, root):
        self.bind = {}
        raw = {k: plainify(v) for k, v in read(text).table.items()}
        self.defs = {k: sh.to_type(v) for k, v in raw.items()}
        self.names = {id(t): n for n, t in self.defs.items()}
        self.root = self.defs[root]
        for name, t in self.defs.items(): self._check_names(t, name)
    def conv_scalar(self, name, v, path, limit=None):
        if name == 'null':
            if isinstance(v, Plain) and v == 'null': return None
            raise sh.Bad(path, 'expected null')
        if name == 'str': return str(v) if isinstance(v, str) else self._no(path, name)
        if name != 'any' and not isinstance(v, Plain): raise sh.Bad(path, f'quoted, so not {name}')
        return super().conv_scalar(name, v, path, limit)
    def _no(self, path, name): raise sh.Bad(path, f'expected {name}')
    def conv_alt(self, alts, v, path):
        if isinstance(v, (dict, list)): return super().conv_alt(alts, v, path)
        if v in [a[1] for a in alts if a[0] == 'lit']: return str(v)
        for a in alts:
            if a[0] != 'name': continue
            try: return self.conv(a, v, path)
            except sh.Bad: pass
        raise sh.Bad(path, f'{str(v)[:40]!r} is not allowed here')
sh.BUILTIN.add('null')
def plainify(v):
    if isinstance(v, dict): return {str(k): plainify(x) for k, x in v.items()}
    if isinstance(v, list): return [plainify(x) for x in v]
    return str(v)

JSON = '''%YAML 2.0
--- &
json: !null | !bool | !int | !float | !str | !array | !object
array: [!json, ...]
object:
  !str: !json
'''
def exact(a, b):
    if type(a) is not type(b): return False
    if isinstance(a, dict): return list(a) == list(b) and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, list): return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return a == b or (a != a and b != b)
if __name__ == '__main__':
    S = Schema2(JSON, 'json')
    print(S.check(read('{"a": 1, "b": "1", "c": null, "d": "null", "e": 1.10, "f": true, "g": [2, {"h": "x"}], "i": plain}\n').docs[0][1]))
    c = collections.Counter()
    root = sys.argv[1]
    for f in sorted(os.listdir(root)):
        p = os.path.join(root, f)
        if os.path.getsize(p) > 300000: continue
        try: t = open(p, encoding='utf-8').read(); j = json.loads(t)
        except Exception: continue
        c['files'] += 1
        d = read(t).docs
        c['exact' if len(d) == 1 and exact(S.check(d[0][1]), j) else 'differs'] += 1
    print('real JSON', dict(c))
    c = collections.Counter(); root = sys.argv[2]
    for f in sorted(os.listdir(root)):
        if not f.startswith('y_'): continue
        b = open(os.path.join(root, f), 'rb').read()
        try: t = b.decode('utf-8', 'surrogatepass'); j = json.loads(t)
        except Exception: c['baseline cannot read'] += 1; continue
        c['files'] += 1
        try:
            d = read(t).docs
            c['exact' if len(d) == 1 and exact(S.check(d[0][1]), j) else 'differs'] += 1
        except No as e: c['refused: ' + re.sub(r' at line \d+', '', str(e))] += 1
    print('JSONTestSuite', dict(c))
    W = '''%YAML 2.0
--- &
free: !str | !list | !map
list: [!free, ...]
map:
  timeout?: !int
  !str: !free
'''
    S = Schema2(W, 'free')
    doc = '---\ntimeout: 30\nname: 30\njobs:\n  - {timeout: 5, retries: 2}\n  - nested: {deep: {timeout: 7}}\n'
    print('wherever a key occurs:', S.check(read(doc).docs[0][1]))
    try: S.check(read('---\na: [{b: {timeout: soon}}]\n').docs[0][1]); print('NOT refused')
    except sh.Bad as e: print('refused:', e)
