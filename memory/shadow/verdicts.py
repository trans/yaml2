"""Each file's verdict, one line per file, for a parser to compare with its own.
The stream is read as Oyl NG reads the public sample: any BOM dropped, `%YAML 2.0` added, and `---`
where no marker comes first (draftcheck.py's framed). Every document is typed by the shadow as an
application's schema with its root (part 2, section 3). The JSON Schema's verdict is on PyYAML's
reading, as in current.py, for reference.
Usage: verdicts.py KIND SHADOW ROOT JSONSCHEMA DIR > FILE.tsv (needs PyYAML and jsonschema)
Columns: kind, file, grammar (reads or refuses), shadow (accepts, refuses, or - if the grammar
refuses), the path the shadow refuses at, the JSON Schema (ok, bad, or - if PyYAML can't read the
file or its root isn't a mapping)."""
import os, re, sys
import yaml, jsonschema
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(here + '/schemacheck.py', encoding='utf-8').read().split("\nif __name__ == '__main__':")[0]
ns = {'__name__': 'sc', '__file__': here + '/schemacheck.py'}
exec(compile(src, 'sc', 'exec'), ns)
read, typed, REFUSED, No = (ns[k] for k in 'read typed REFUSED No'.split())
kind, shadowfile, root, jsfile, top = sys.argv[1:6]
class Core(yaml.SafeLoader): pass
Core.yaml_implicit_resolvers = {k: [(t, r) for t, r in v if t not in ('tag:yaml.org,2002:bool', 'tag:yaml.org,2002:timestamp')]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()}
Core.add_implicit_resolver('tag:yaml.org,2002:bool', re.compile(r'^(?:true|True|TRUE|false|False|FALSE)$'), list('tTfF'))
js = json = None
import json
js = json.load(open(jsfile)); V = jsonschema.validators.validator_for(js, default=jsonschema.Draft7Validator)(js)
app = (open(shadowfile, encoding='utf-8').read(), root)
print('kind\tfile\tgrammar\tshadow\tpath\tjson-schema')
for f in sorted(os.listdir(top)):
    if not f.endswith(('.yml', '.yaml')): continue
    b = open(os.path.join(top, f), 'rb').read()
    try: t = b.decode('utf-8')
    except UnicodeDecodeError: print(f'{kind}\t{f}\tnot UTF-8\t-\t\t-'); continue
    if t.startswith('﻿'): t = t[1:]
    try:
        c = yaml.load(t, Loader=Core); j = ('ok' if not any(True for _ in V.iter_errors(c)) else 'bad') if isinstance(c, dict) else '-'
    except Exception: j = '-'
    try: read(t)
    except (No, RecursionError): print(f'{kind}\t{f}\trefuses\t-\t\t{j}'); continue
    try: typed(t, app); sh, path = 'accepts', ''
    except REFUSED as e: sh, path = 'refuses', str(e).split(':')[0]
    print(f'{kind}\t{f}\treads\t{sh}\t{path}\t{j}')
