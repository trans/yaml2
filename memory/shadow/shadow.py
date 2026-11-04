"""A prototype of YAML 2.0's typed shadow: type a Rule 1 document with a schema.

Stands in for a 2.0 parser with PyYAML's BaseLoader, which reads every scalar
as a string. A schema is read the way a 2.0 parser would read it: `!` is an
ordinary character, so `read_schema` only quotes what PyYAML would otherwise
take for a tag.

A value starting with `!` is a type expression, any other value a literal:

    expr  := alt ('|' alt)*
    alt   := name | '[' expr '*' ']' | '[' expr (',' expr)* ']' | 'literal'

A key ending in `?` may be absent or empty (empty types as None). A key that is
a type expression (`!str`) takes every key not named. A key ending in `*` takes
keys with that prefix. Mappings are closed otherwise. Alternatives are chosen by shape, never by how text looks: at most
one scalar type, at most one sequence, and mappings told apart by their
required keys and literals.
"""
import re
import yaml

BUILTIN = {'str', 'int', 'float', 'bool', 'any'}


class SchemaError(Exception):
    pass


class Bad(Exception):
    def __init__(self, path, msg):
        self.path, self.msg = path, msg
        super().__init__(f'{path or "/"}: {msg}')


def _quote(text):
    return "'" + text.replace("'", "''") + "'"


def _prepare(doc):
    """Quote `!` keys and values, and `<<: *x`, for PyYAML's sake."""
    out = []
    for line in doc.splitlines():
        code = re.sub(r'\s+#.*$', '', line)
        if not code.strip() or code.lstrip().startswith('#'):
            continue
        m = re.match(r'^(\s*)([^\s:]+):(?:\s+(.*))?$', code)
        if not m:
            raise SchemaError(f'cannot read: {line}')
        ind, key, val = m.group(1), m.group(2), m.group(3)
        if key.startswith('!') or key == '<<':
            key = _quote(key)
        if val and (val.startswith('!') or val.startswith('*') or val.startswith('[*')):
            val = _quote(val)
        out.append(f'{ind}{key}:' + (f' {val}' if val else ''))
    return '\n'.join(out) + '\n'


def parse_expr(s):
    s = s.strip()
    parts, depth, cur, quoted = [], 0, '', False
    for c in s:
        if c == "'":
            quoted = not quoted
        if not quoted:
            depth += c == '['
            depth -= c == ']'
            if c == '|' and depth == 0:
                parts.append(cur)
                cur = ''
                continue
        cur += c
    parts.append(cur)
    if len(parts) > 1:
        return ('alt', [parse_expr(p) for p in parts])
    if s.startswith("'") and s.endswith("'"):
        return ('lit', s[1:-1])
    if s.startswith('[') and s.endswith(']'):
        inner = s[1:-1].strip()
        if inner.endswith('*'):
            return ('many', parse_expr(inner[:-1]))
        items, depth, cur = [], 0, ''
        for c in inner:
            depth += c == '['
            depth -= c == ']'
            if c == ',' and depth == 0:
                items.append(cur)
                cur = ''
            else:
                cur += c
        items.append(cur)
        return ('tuple', [parse_expr(i) for i in items])
    if not re.fullmatch(r'[A-Za-z_][\w-]*', s):
        raise SchemaError(f'bad type: {s}')
    return ('name', s)


def to_type(value):
    if isinstance(value, dict):
        fields, any_key, prefixes = {}, None, []
        for k, v in value.items():
            if k.startswith('!'):
                any_key = to_type(v)
            elif k.endswith('*'):
                prefixes.append((k[:-1], to_type(v)))
            elif k.endswith('?'):
                fields[k[:-1]] = (to_type(v), True)
            else:
                fields[k] = (to_type(v), False)
        return ('map', fields, any_key, prefixes)
    if isinstance(value, list):
        raise SchemaError('a sequence in a schema is written as a type expression')
    if value.startswith('!'):
        return parse_expr(value[1:])
    return ('lit', value)


class Schema:
    def __init__(self, text, bind=None):
        # App code bound to named types: name -> fn(value) -> typed, or raises
        # ValueError. A schema only names types; it never picks the code.
        self.bind = bind or {}
        self.defs = {}
        raw = {}
        root = None
        lines = [l for l in text.splitlines() if not l.startswith('%YAML')]
        docs, cur, marked = [], [], False
        for line in lines:
            if line.startswith('---'):
                if cur:
                    docs.append((marked, '\n'.join(cur)))
                cur, marked = [], line.strip() == '--- &'
            else:
                cur.append(line)
        if cur:
            docs.append((marked, '\n'.join(cur)))
        for is_def, body in docs:
            data = yaml.load(_prepare(body), Loader=yaml.BaseLoader)
            if not is_def:
                root = data
                continue
            for name, entry in data.items():
                if name in BUILTIN:
                    raise SchemaError(f'{name} is a built-in type')
                raw[name] = self._merge(entry, raw, name)
        self.defs = {k: to_type(v) for k, v in raw.items()}
        self.names = {id(t): n for n, t in self.defs.items()}
        self.root = to_type(self._merge(root, raw, 'root'))
        for name, t in self.defs.items():
            self._check_alts(t, name)
        self._check_alts(self.root, 'root')

    @staticmethod
    def _merge(entry, raw, name):
        """A `<<` at the top of an entry, of earlier entries only."""
        if not (isinstance(entry, dict) and '<<' in entry):
            return entry
        merged = {}
        for ref in re.findall(r'\*([\w-]+)', entry['<<']):
            if ref not in raw:
                raise SchemaError(f'{name}: no earlier entry {ref}')
            merged.update(raw[ref])
        merged.update({k: v for k, v in entry.items() if k != '<<'})
        return merged

    def flat(self, t, seen=()):
        """The alternatives of t, with names resolved."""
        if t[0] == 'alt':
            return [a for x in t[1] for a in self.flat(x, seen)]
        if t[0] == 'name' and t[1] not in BUILTIN:
            if t[1] not in self.defs:
                raise SchemaError(f'no type {t[1]}')
            if t[1] in seen:
                return [t]
            inner = self.flat(self.defs[t[1]], seen + (t[1],))
            if len(inner) == 1 and inner[0][0] == 'name':
                return [t]      # a named scalar keeps its name
            return inner
        return [t]

    def _check_alts(self, t, where):
        if t[0] == 'alt':
            alts = self.flat(t)
            scalars = [a for a in alts if a[0] == 'name']
            seqs = [a for a in alts if a[0] in ('many', 'tuple')]
            if len(scalars) > 1:
                raise SchemaError(f'{where}: more than one scalar alternative: {scalars}')
            if len(seqs) > 1:
                raise SchemaError(f'{where}: more than one sequence alternative')
            for x in t[1]:
                self._check_alts(x, where)
        elif t[0] == 'map':
            for k, (ft, _) in t[1].items():
                self._check_alts(ft, f'{where}.{k}')
            if t[2]:
                self._check_alts(t[2], where)
        elif t[0] == 'many':
            self._check_alts(t[1], where)
        elif t[0] == 'tuple':
            for x in t[1]:
                self._check_alts(x, where)

    def check(self, value):
        return self.conv(self.root, value, '')

    def conv(self, t, v, path):
        kind = t[0]
        if kind == 'alt':
            return self.conv_alt(self.flat(t), v, path)
        if kind == 'name':
            if t[1] in BUILTIN:
                return self.conv_scalar(t[1], v, path)
            out = self.conv(self.defs[t[1]], v, path)
            if t[1] in self.bind:
                try:
                    return self.bind[t[1]](out)
                except ValueError as e:
                    raise Bad(path, f'{t[1]}: {e}')
            return out
        if kind == 'lit':
            if v != t[1]:
                raise Bad(path, f'expected {t[1]!r}, got {str(v)[:40]!r}')
            return v
        if kind == 'many':
            if not isinstance(v, list):
                raise Bad(path, 'expected a sequence')
            return [self.conv(t[1], x, f'{path}/{i}') for i, x in enumerate(v)]
        if kind == 'tuple':
            if not isinstance(v, list) or len(v) != len(t[1]):
                raise Bad(path, f'expected a sequence of {len(t[1])}')
            return [self.conv(a, x, f'{path}/{i}') for i, (a, x) in enumerate(zip(t[1], v))]
        if kind == 'map':
            return self.conv_map(t, v, path)
        raise SchemaError(kind)

    def conv_scalar(self, name, v, path):
        if name == 'any':
            return v
        if not isinstance(v, str):
            raise Bad(path, f'expected {name}')
        if name == 'str':
            return v
        if name == 'bool' and v in ('true', 'false'):
            return v == 'true'
        if name == 'int' and re.fullmatch(r'-?[0-9]+', v):
            return int(v)
        if name == 'float' and re.fullmatch(r'-?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?', v):
            return float(v)
        raise Bad(path, f'expected {name}, got {v[:40]!r}')

    def conv_map(self, t, v, path):
        if not isinstance(v, dict):
            raise Bad(path, 'expected a mapping')
        out = {}
        for key, (ft, optional) in t[1].items():
            if key not in v:
                if not optional:
                    raise Bad(path, f'missing {key}')
                continue
            if optional and v[key] == '':
                out[key] = None
            else:
                out[key] = self.conv(ft, v[key], f'{path}/{key}')
        for key in v:
            if key in t[1]:
                continue
            for prefix, pt in t[3]:
                if key.startswith(prefix):
                    out[key] = self.conv(pt, v[key], f'{path}/{key}')
                    break
            else:
                if t[2] is None:
                    raise Bad(path, f'unknown key {key}')
                out[key] = self.conv(t[2], v[key], f'{path}/{key}')
        return out

    def bound(self, t, value, path):
        """Apply the code bound to a named alternative, if any."""
        name = self.names.get(id(t))
        if name in self.bind:
            try:
                return self.bind[name](value)
            except ValueError as e:
                raise Bad(path, f'{name}: {e}')
        return value

    def conv_alt(self, alts, v, path):
        if isinstance(v, dict):
            maps = [a for a in alts if a[0] == 'map']
            fits = [m for m in maps if self.discriminates(m, v)]
            if len(fits) == 1:
                return self.bound(fits[0], self.conv_map(fits[0], v, path), path)
            if not maps:
                raise Bad(path, 'a mapping is not allowed here')
            raise Bad(path, f'{len(fits)} of {len(maps)} mapping alternatives fit')
        if isinstance(v, list):
            seqs = [a for a in alts if a[0] in ('many', 'tuple')]
            if not seqs:
                raise Bad(path, 'a sequence is not allowed here')
            return self.bound(seqs[0], self.conv(seqs[0], v, path), path)
        lits = [a[1] for a in alts if a[0] == 'lit']
        if v in lits:
            return v
        scalars = [a for a in alts if a[0] == 'name']
        if scalars:
            return self.conv(scalars[0], v, path)
        raise Bad(path, f'{v[:40]!r} is not allowed here')

    def discriminates(self, m, v):
        for key, (ft, optional) in m[1].items():
            if key not in v:
                if not optional:
                    return False
            elif ft[0] == 'lit' and v[key] != ft[1]:
                return False
        return True


def load(path, bind=None):
    return Schema(open(path).read(), bind)
