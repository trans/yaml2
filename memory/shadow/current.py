"""Each real schema, read by the current checker, against the JSON Schema it was written from.
Two readings of each file: the 2.0 grammar, where it reads as written, and PyYAML with quoted
scalars marked, so a file the grammar refuses still gets compared.
Usage: current.py NAME SHADOW ROOT JSONSCHEMA DIR... (needs PyYAML and jsonschema)
A DIR ending in Projects or .config is searched for .github/workflows only."""
import collections, hashlib, json, os, re, sys
import yaml, jsonschema
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(here + '/schemacheck.py', encoding='utf-8').read().split("\nif __name__ == '__main__':")[0]
ns = {'__name__': 'sc', '__file__': here + '/schemacheck.py'}
exec(compile(src, 'sc', 'exec'), ns)
read, Schema, Quoted, REFUSED, No, Bad = (ns[k] for k in 'read Schema Quoted REFUSED No Bad'.split())
kind, shadowfile, root, jsfile = sys.argv[1:5]; dirs = sys.argv[5:]
class Core(yaml.SafeLoader): pass
Core.yaml_implicit_resolvers = {k: [(t, r) for t, r in v if t not in ('tag:yaml.org,2002:bool', 'tag:yaml.org,2002:timestamp')]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()}
Core.add_implicit_resolver('tag:yaml.org,2002:bool', re.compile(r'^(?:true|True|TRUE|false|False|FALSE)$'), list('tTfF'))
class Keep(yaml.BaseLoader):
    def construct_scalar(s, n):
        v = super().construct_scalar(n)
        return Quoted(v) if n.style else v
def flatten(node):
    if isinstance(node, list): return [flatten(x) for x in node]
    if not isinstance(node, dict): return node
    out = {}; src = node.get('<<')
    for m in ([src] if isinstance(src, dict) else src if isinstance(src, list) else []):
        if isinstance(m, dict):
            for k, v in flatten(m).items(): out.setdefault(k, v)
    if src is not None and not isinstance(src, (dict, list)): out['<<'] = src
    out.update({k: flatten(v) for k, v in node.items() if k != '<<'})
    return out
def files():
    seen = set()
    for r in dirs:
        for d, ds, fs in os.walk(r):
            ds[:] = [x for x in ds if x not in ('node_modules', '.git') or d.endswith('/.github')]
            for f in fs:
                if not f.endswith(('.yml', '.yaml')): continue
                if r.endswith(('Projects', '.config')) and not d.endswith('/.github/workflows'): continue
                b = open(os.path.join(d, f), 'rb').read(); h = hashlib.sha256(b).digest()
                if h not in seen: seen.add(h); yield os.path.join(d, f), b
js = json.load(open(jsfile)); V = jsonschema.validators.validator_for(js, default=jsonschema.Draft7Validator)(js)
own = Schema(read(open(shadowfile, encoding='utf-8').read()).table, root)
T = collections.Counter(); G = collections.Counter(); why = collections.defaultdict(collections.Counter); ex = {}
def short(e): return re.sub(r"'[^']*'", "'…'", re.sub(r'/[0-9]+', '/*', re.sub(r'(services|volumes|networks|jobs|secrets|configs|env|with|outputs|inputs)/[^/: ]+', r'\1/K', str(e))))[:88]
total = 0
for p, b in files():
    total += 1
    try: t = b.decode('utf-8')
    except UnicodeDecodeError: T['not UTF-8'] += 1; continue
    if t.startswith('﻿'): t = t[1:]
    try:
        c = yaml.load(t, Loader=Core); s = flatten(yaml.load(t, Loader=Keep))
    except Exception: T['1.x parser refuses'] += 1; c = s = None
    if isinstance(c, dict):
        errs = list(V.iter_errors(c)); js_ok = not errs
        try: own.check(s); sh = True; msg = ''
        except REFUSED as e: sh = False; msg = short(e)
        T[f'schema {"ok " if js_ok else "bad"} shadow {"ok " if sh else "bad"}'] += 1
        if js_ok and not sh: why['refused by the shadow only'][msg] += 1; ex.setdefault(msg, p)
        if sh and not js_ok:
            m = errs[0]; k = '/'.join('*' if isinstance(x, int) else str(x) for x in m.absolute_path)[-40:] + ' ' + m.message[:50]
            k = re.sub(r"'[^']*'", "'…'", k); why['refused by the JSON Schema only'][k] += 1; ex.setdefault(k, p)
    elif c is not None: T['root is not a mapping'] += 1
    try:
        r = read(t); G['grammar reads'] += 1
    except No: G['grammar refuses'] += 1; continue
    except RecursionError: G['recursion'] += 1; continue
    ok = True; msg = ''
    for name, v in r.docs:
        try: own.check(v)
        except REFUSED as e: ok = False; msg = short(e)
    if isinstance(c, dict):
        G[f'  schema {"ok " if js_ok else "bad"} shadow {"ok " if ok else "bad"}'] += 1
        if ok != sh: G['  grammar and PyYAML readings disagree'] += 1; ex.setdefault('reading ' + msg, p); why['readings disagree'][msg] += 1
print(kind, total, 'files, unique by hash')
print('every file (PyYAML reading):'); [print(f'  {n:5} {k}') for k, n in sorted(T.items())]
print('files the grammar reads:'); [print(f'  {n:5} {k}') for k, n in sorted(G.items())]
for k, c in why.items():
    print(k + ':')
    for m, n in c.most_common(14): print(f'  {n:4} {m}   [{os.path.basename(ex.get(m, ex.get("reading " + m, "")))}]')
