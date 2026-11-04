"""A prototype of YAML 2.0's typed shadow: type a Rule 1 document with a schema.

Stands in for a 2.0 parser with PyYAML's BaseLoader, which reads every scalar
as a string. A schema is read the way a 2.0 parser would read it: `!` is an
ordinary character, so `read_schema` only quotes what PyYAML would otherwise
take for a tag.

`!name` is a type and bare text a literal, on every part of a value:

    expr  := atom ('|' atom)*
    atom  := '!' name | '[' expr (',' expr)* [',' '...'] ']' | '' | literal

`...` repeats the item before it, any number of times, none included.

A key ending in `?` may be absent or empty (empty types as None). A key that is
a type (`!str`, `!str(/^x-/)`) takes every key it fits and that isn't named. A
scalar type may carry a limit: `!int(0..100)`, `!str(1..)`, `!str(/regex/)`.
Mappings are closed otherwise. Alternatives are chosen by shape, never by how text looks: at most
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
    """Quote `!` keys and values, and turn `<< *x` into a key, for PyYAML's sake."""
    out = []
    for line in doc.splitlines():
        code = re.sub(r'\s+#.*$', '', line)
        if not code.strip() or code.lstrip().startswith('#'):
            continue
        m = re.match(r'^(\s*(?:- )*)(.*)$', code)
        ind, rest = m.group(1), m.group(2)
        m = re.match(r'^<< +(\*\S+)$', rest)
        if m:
            # PyYAML would keep only the last of a repeated key, so join them.
            if out and out[-1].startswith(f"{ind}'<<': "):
                out[-1] = out[-1][:-1] + f" {m.group(1)}'"
            else:
                out.append(f"{ind}'<<': {_quote(m.group(1))}")
            continue
        m = re.match(r'^([^\s:\[{]+):(?:\s+(.*))?$', rest)
        if not m:
            # A sequence item that is a value, not a key: `- !str`, `- ...`.
            out.append(ind + (_quote(rest) if rest[0] in '!*[{' else rest))
            continue
        key, val = m.group(1), m.group(2)
        if key == '<<':
            raise SchemaError('`<<:` is an error: merge with `<< *a`, or quote the key')
        if key.startswith('!'):
            key = _quote(key)
        if val and val[0] in '!*[{':
            val = _quote(val)
        out.append(f'{ind}{key}:' + (f' {val}' if val else ''))
    return '\n'.join(out) + '\n'


def split_top(s, sep):
    parts, depth, cur = [], 0, ''
    for c in s:
        depth += c in '[{('
        depth -= c in ']})'
        if c == sep and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += c
    return parts + [cur]


def parse_limit(text, whole):
    """`0..100`, `1..`, `..64`, or `/regex/`."""
    if len(text) > 1 and text.startswith('/') and text.endswith('/'):
        return ('re', re.compile(text[1:-1]))
    m = re.fullmatch(r'(-?[0-9.]*?)\.\.(-?[0-9.]*)', text)
    if not m:
        raise SchemaError(f'bad limit: {whole}')
    lo, hi = (float(x) if x else None for x in m.groups())
    return ('range', lo, hi)


def parse_expr(s):
    s = s.strip()
    parts = split_top(s, '|')
    if len(parts) > 1:
        return ('alt', [parse_expr(p) for p in parts])
    if s == "''":
        return ('lit', '')
    if s.startswith('!'):
        m = re.fullmatch(r'!([A-Za-z_][\w-]*)(?:\((.*)\))?', s, re.S)
        if not m:
            raise SchemaError(f'bad type: {s}')
        if m.group(2) is None:
            return ('name', m.group(1))
        if m.group(1) not in ('str', 'int', 'float'):
            raise SchemaError(f'{s}: only str, int and float take a limit')
        return ('name', m.group(1), parse_limit(m.group(2), s))
    if s.startswith('[') and s.endswith(']'):
        items = [i.strip() for i in split_top(s[1:-1], ',')]
        rest = None
        if items[-1] == '...':
            items.pop()
            rest = parse_expr(items.pop())
        return ('seq', [parse_expr(i) for i in items], rest)
    if s.startswith('{') and s.endswith('}'):
        return to_type(dict(i.split(': ', 1) for i in
                            (x.strip() for x in split_top(s[1:-1], ','))))
    return ('lit', s)


def to_type(value):
    if isinstance(value, dict):
        fields, rows = {}, []
        for k, v in value.items():
            if k.startswith('!'):
                rows.append((parse_expr(k), to_type(v)))
            elif k.endswith('?'):
                fields[k[:-1]] = (to_type(v), True)
            else:
                fields[k] = (to_type(v), False)
        return ('map', fields, rows)
    if isinstance(value, list):
        items, rest = list(value), None
        if items and items[-1] == '...':
            items.pop()
            rest = to_type(items.pop())
        return ('seq', [to_type(i) for i in items], rest)
    return parse_expr(value)


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
            self._check_names(t, name)
        self._check_names(self.root, 'root')
        for name, t in self.defs.items():
            self._check_alts(t, name)
        self._check_alts(self.root, 'root')

    @staticmethod
    def _merge(entry, raw, name):
        """A `<<` at the top of an entry, of earlier entries only."""
        if not (isinstance(entry, dict) and '<<' in entry):
            return entry
        if next(iter(entry)) != '<<':
            raise SchemaError(f'{name}: `<<` must come first')
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
            seqs = [a for a in alts if a[0] == 'seq']
            if len(scalars) > 1:
                raise SchemaError(f'{where}: more than one scalar alternative: {scalars}')
            if len(seqs) > 1:
                raise SchemaError(f'{where}: more than one sequence alternative')
            for x in t[1]:
                self._check_alts(x, where)
        elif t[0] == 'map':
            for k, (ft, _) in t[1].items():
                self._check_alts(ft, f'{where}.{k}')
            for _, vt in t[2]:
                self._check_alts(vt, where)
        elif t[0] == 'seq':
            for x in t[1] + ([t[2]] if t[2] else []):
                self._check_alts(x, where)

    def _check_names(self, t, where):
        """Every name is built in or in the table, used or not by any document."""
        if t[0] == 'name' and t[1] not in BUILTIN and t[1] not in self.defs:
            raise SchemaError(f'{where}: unknown type !{t[1]}')
        if t[0] == 'alt':
            for x in t[1]:
                self._check_names(x, where)
        elif t[0] == 'seq':
            for x in t[1] + ([t[2]] if t[2] else []):
                self._check_names(x, where)
        elif t[0] == 'map':
            for k, (ft, _) in t[1].items():
                self._check_names(ft, f'{where}.{k}')
            for kt, vt in t[2]:
                self._check_names(kt, where)
                self._check_names(vt, where)

    def check(self, value):
        return self.conv(self.root, value, '')

    def conv(self, t, v, path):
        kind = t[0]
        if kind == 'alt':
            return self.conv_alt(self.flat(t), v, path)
        if kind == 'name':
            if t[1] in BUILTIN:
                return self.conv_scalar(t[1], v, path, t[2] if len(t) > 2 else None)
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
        if kind == 'seq':
            fixed, rest = t[1], t[2]
            if not isinstance(v, list):
                raise Bad(path, 'expected a sequence')
            if len(v) < len(fixed) or (rest is None and len(v) != len(fixed)):
                raise Bad(path, f'wrong length: {len(v)}')
            return [self.conv(fixed[i] if i < len(fixed) else rest, x, f'{path}/{i}')
                    for i, x in enumerate(v)]
        if kind == 'map':
            return self.conv_map(t, v, path)
        raise SchemaError(kind)

    def conv_scalar(self, name, v, path, limit=None):
        if name == 'any':
            return v
        if not isinstance(v, str):
            raise Bad(path, f'expected {name}')
        if name == 'str':
            out = v
        elif name == 'bool' and v in ('true', 'false'):
            out = v == 'true'
        elif name == 'int' and re.fullmatch(r'-?[0-9]+', v):
            out = int(v)
        elif name == 'float' and re.fullmatch(r'-?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?', v):
            out = float(v)
        else:
            raise Bad(path, f'expected {name}, got {v[:40]!r}')
        if limit and limit[0] == 're':
            if not limit[1].search(v):
                raise Bad(path, f'{v[:40]!r} does not match')
        elif limit:
            size = len(out) if name == 'str' else out
            if (limit[1] is not None and size < limit[1]) or (limit[2] is not None and size > limit[2]):
                raise Bad(path, f'{v[:40]!r} is out of range')
        return out

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
            for kt, vt in t[2]:
                try:
                    self.conv(kt, key, path)
                except Bad:
                    continue
                out[key] = self.conv(vt, v[key], f'{path}/{key}')
                break
            else:
                raise Bad(path, f'unknown key {key}')
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
            seqs = [a for a in alts if a[0] == 'seq']
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
