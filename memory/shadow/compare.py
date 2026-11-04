"""Run a shadow on real files, against the JSON Schema it was written from.
Usage: compare.py workflows|compose SCHEMA.json ROOT... (needs jsonschema)"""
import collections, copy, hashlib, json, os, random, re, sys
import yaml, jsonschema
import shadow


class Core(yaml.SafeLoader):
    """YAML 1.2 Core, near enough: `on` is a string, as GitHub reads it."""


Core.yaml_implicit_resolvers = {k: [(t, r) for t, r in v if t not in (
    'tag:yaml.org,2002:bool', 'tag:yaml.org,2002:timestamp')]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()}
Core.add_implicit_resolver('tag:yaml.org,2002:bool',
    re.compile(r'^(?:true|True|TRUE|false|False|FALSE)$'), list('tTfF'))


def _expr(v):
    if not re.search(r'\$\{\{.*\}\}', v, re.S):
        raise ValueError('expected ${{ ... }}')
    return v


def _flag(v):
    return v == 'true' if v in ('true', 'false') else _expr(v)


def _number(v):
    return float(v) if re.fullmatch(r'-?[0-9]+(\.[0-9]+)?', v) else _expr(v)


# What GitHub's own code would bind. The schema itself holds no patterns.
BINDINGS = {'expr': _expr, 'flag': _flag, 'number': _number}


def corpus(roots, kind):
    seen = set()
    for root in roots:
        for d, ds, fs in os.walk(root, followlinks=False):
            ds[:] = [x for x in ds if x not in ('node_modules', '.git') or d.endswith('/.github')]
            for f in fs:
                if kind == 'workflows':
                    wanted = d.endswith('/.github/workflows') and f.endswith(('.yml', '.yaml'))
                else:
                    wanted = re.fullmatch(r'(docker-)?compose([._-][\w.-]*)?\.ya?ml', f)
                if wanted:
                    b = open(os.path.join(d, f), 'rb').read()
                    h = hashlib.sha256(b).digest()
                    if h not in seen:
                        seen.add(h)
                        yield os.path.join(d, f), b


def flatten(node):
    """BaseLoader leaves `<<` as a key; apply it, as a 2.0 parser would."""
    if isinstance(node, list):
        return [flatten(x) for x in node]
    if not isinstance(node, dict):
        return node
    out = {}
    src = node.get('<<')
    for m in ([src] if isinstance(src, dict) else src if isinstance(src, list) else []):
        if isinstance(m, dict):
            for k, v in flatten(m).items():
                out.setdefault(k, v)
    if src is not None and not isinstance(src, (dict, list)):
        out['<<'] = src
    local = {k: flatten(v) for k, v in node.items() if k != '<<'}
    out.update(local)
    return out


def norm(path):
    ep = list(path)
    if len(ep) > 1 and ep[0] == 'jobs':
        ep[1] = 'JOB'
    for i, x in enumerate(ep[:-1]):
        if x in ('with', 'env', 'outputs', 'inputs', 'secrets', 'services'):
            ep[i + 1] = 'KEY'
        if x == 'matrix' and ep[i + 1] not in ('include', 'exclude'):
            ep[i + 1] = 'KEY'
    return '/'.join('*' if isinstance(x, int) else str(x) for x in ep)[:50]


def spots(node, path=()):
    """Every position in a tree."""
    yield path, node
    if isinstance(node, dict):
        for k, v in node.items():
            yield from spots(v, path + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from spots(v, path + (i,))


def setat(tree, path, fn):
    t = tree
    for p in path[:-1]:
        t = t[p]
    if fn is None:
        del t[path[-1]]
    else:
        t[path[-1]] = fn


def mutate(rng, s, c):
    """One mutation applied to both trees, the same place in each."""
    pos = [p for p, _ in spots(s) if p]
    rng.shuffle(pos)
    def at(tree, p):
        for x in p:
            tree = tree[x]
        return tree
    return pos, at


def main():
    kind = sys.argv[1]
    schema = json.load(open(sys.argv[2]))
    validator = jsonschema.validators.validator_for(schema, default=jsonschema.Draft7Validator)(schema)
    here = os.path.dirname(os.path.abspath(__file__))
    file = 'github-workflow.shadow' if kind == 'workflows' else 'compose.shadow'
    sh = shadow.load(os.path.join(here, file))
    bound = shadow.load(os.path.join(here, file), BINDINGS if kind == 'workflows' else None)
    tally = collections.Counter()
    reasons = {'shadow_only': collections.Counter(), 'schema_only': collections.Counter()}
    good = []
    mines = collections.Counter()
    typed_leaves = collections.Counter()
    for path, b in corpus(sys.argv[3:], kind):
        try:
            s = flatten(yaml.load(b, Loader=yaml.BaseLoader))
            c = yaml.load(b, Loader=Core)
            old = yaml.load(b, Loader=yaml.SafeLoader)
        except Exception:
            tally['unparsable'] += 1
            continue
        if not isinstance(s, dict):
            tally['not a mapping'] += 1
            continue
        try:
            js_errs = list(validator.iter_errors(c))
        except Exception as e:
            js_errs = [e]
        js_ok = not js_errs
        try:
            bound.check(s)
        except shadow.Bad as e:
            tally['bound shadow rejects'] += 1
        try:
            typed = sh.check(s)
            sh_ok, why = True, ''
        except shadow.Bad as e:
            sh_ok, why = False, e.path[-44:] + ' ' + re.sub(r"'[^']*'", "'…'", e.msg)
        tally[f'schema {"ok " if js_ok else "bad"} shadow {"ok " if sh_ok else "bad"}'] += 1
        if js_ok and sh_ok:
            good.append((s, c))
        if js_ok and not sh_ok:
            reasons['shadow_only'][why] += 1
            reasons.setdefault('files', []).append((path, str(shadow.Bad)))
        if not js_ok:
            print('schema rejects', os.path.relpath(path, os.path.expanduser('~')), '|', str(getattr(js_errs[0], 'message', js_errs[0]))[:90], '| shadow:', why[:70])
        if sh_ok and not js_ok:
            reasons['schema_only'][str(getattr(js_errs[0], 'message', js_errs[0]))[:70]] += 1
        if sh_ok:
            for _, leaf in spots(typed):
                if not isinstance(leaf, (dict, list)):
                    typed_leaves[type(leaf).__name__] += 1
        # Values that 1.2 Core changes from their text.
        def walk(raw, val):
            if isinstance(raw, dict) and isinstance(val, dict):
                for k, v in raw.items():
                    if k in val:
                        walk(v, val[k])
            elif isinstance(raw, list) and isinstance(val, list):
                for a, b2 in zip(raw, val):
                    walk(a, b2)
            elif isinstance(raw, str) and isinstance(val, float) and str(val) != raw:
                mines['core: number loses its text'] += 1
                mines['example ' + raw + ' -> ' + str(val)] += 1
            elif isinstance(raw, str) and isinstance(val, int) and not isinstance(val, bool) and str(val) != raw:
                mines['core: int loses its text'] += 1
        walk(s, c)
        def walk11(raw, val):
            if isinstance(raw, dict) and isinstance(val, dict):
                for k, v in raw.items():
                    if k in val:
                        walk11(v, val[k])
            elif isinstance(raw, list) and isinstance(val, list):
                for a, b2 in zip(raw, val):
                    walk11(a, b2)
            elif isinstance(raw, str) and raw != '' and not isinstance(val, (str, type(None))):
                if not (isinstance(val, bool) and raw in ('true', 'false')) and str(val) != raw:
                    mines['1.1 changes a value'] += 1
                    mines['1.1 example ' + raw[:24] + ' -> ' + str(val)[:24]] += 1
        walk11(s, old)
        if True in old:
            mines['1.1: the key on reads as true'] += 1

    print('--- corpus'); [print(f'{v:5} {k}') for k, v in sorted(tally.items())]
    print('--- schema accepts, shadow rejects'); [print(f'{v:5} {k}') for k, v in reasons['shadow_only'].most_common(12)]
    print('--- shadow accepts, schema rejects'); [print(f'{v:5} {k}') for k, v in reasons['schema_only'].most_common(12)]
    print('--- typed leaves', dict(typed_leaves))
    print('--- mines avoided', [f'{k}: {v}' for k, v in mines.most_common(14)])

    # Mutations: the same damage in both trees. Does the shadow see what the
    # JSON Schema sees?
    rng = random.Random(2026)
    kinds = ['delete a key', 'add an unknown key', 'scalar to sequence', 'scalar to mapping',
             'sequence to scalar', 'mapping to scalar', 'bad scalar value']
    res = {k: collections.Counter() for k in kinds}
    bslip, extra = collections.Counter(), collections.Counter()
    bcaught = 0
    slip = collections.Counter()
    for kind in kinds:
        n = 0
        tries = 0
        while n < 1500 and tries < 60000:
            tries += 1
            s, c = copy.deepcopy(rng.choice(good))
            pos, at = mutate(rng, s, c)
            done = False
            for p in pos:
                v = at(s, p)
                try:
                    cv = at(c, p)
                except (KeyError, IndexError, TypeError):
                    continue
                is_scalar = not isinstance(v, (dict, list))
                if kind == 'delete a key' and isinstance(p[-1], str):
                    setat(s, p, None); setat(c, p, None); done = True
                elif kind == 'add an unknown key' and isinstance(v, dict):
                    v['zzz_unknown'] = 'x'; cv['zzz_unknown'] = 'x'; done = True
                elif kind == 'scalar to sequence' and is_scalar:
                    setat(s, p, ['x']); setat(c, p, ['x']); done = True
                elif kind == 'scalar to mapping' and is_scalar:
                    setat(s, p, {'a': 'x'}); setat(c, p, {'a': 'x'}); done = True
                elif kind == 'sequence to scalar' and isinstance(v, list):
                    setat(s, p, 'x'); setat(c, p, 'x'); done = True
                elif kind == 'mapping to scalar' and isinstance(v, dict):
                    setat(s, p, 'x'); setat(c, p, 'x'); done = True
                elif kind == 'bad scalar value' and is_scalar:
                    setat(s, p, 'zzz_bad'); setat(c, p, 'zzz_bad'); done = True
                if done:
                    hit = p
                    break
            if not done:
                continue
            n += 1
            js_bad = any(True for _ in validator.iter_errors(c))
            try:
                sh.check(s); sh_bad = False
            except shadow.Bad:
                sh_bad = True
            try:
                bound.check(s); bd_bad = False
            except shadow.Bad:
                bd_bad = True
            if js_bad and not bd_bad:
                bslip[kind] += 1
            if js_bad and bd_bad:
                bcaught += 1
            if sh_bad and not js_bad:
                extra[kind + ': ' + norm(hit)] += 1
            res[kind][('schema rejects' if js_bad else 'schema accepts', 'shadow rejects' if sh_bad else 'shadow accepts')] += 1
            if js_bad and not sh_bad:
                slip[kind + ': ' + norm(hit)] += 1
    print('--- mutations (kind: both reject / only schema rejects / only shadow rejects / both accept)')
    rr, ar, ss, aa = ('schema rejects', 'shadow rejects'), ('schema rejects', 'shadow accepts'), ('schema accepts', 'shadow rejects'), ('schema accepts', 'shadow accepts')
    t = collections.Counter()
    for k in kinds:
        print(f'{k:22} {res[k][rr]:5} {res[k][ar]:5} {res[k][ss]:5} {res[k][aa]:5}')
        t.update(res[k])
    print(f'{"total":22} {t[rr]:5} {t[ar]:5} {t[ss]:5} {t[aa]:5}   caught {100*t[rr]/(t[rr]+t[ar]):.1f}% of what the schema rejects')
    print(f'with bindings: caught {bcaught} of {t[rr]+t[ar]} ({100*bcaught/(t[rr]+t[ar]):.1f}%)', dict(bslip))
    print('--- what only the schema rejects, unbound'); [print(f'{v:5} {k}') for k, v in slip.most_common(22)]
    print('--- what only the shadow rejects'); [print(f'{v:5} {k}') for k, v in extra.most_common(12)]


main()
