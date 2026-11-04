"""Can named types and app bindings rebuild objects, with nothing new in the
schema? A stand-in for Ruby serializing through a schema."""
import base64, datetime, sys, yaml, shadow

SCHEMA = """%YAML 2.0
--- &
date: !str
blob: !str
tag-set: [!str, ...]
point:
  x: !float
  y: !float
circle:
  kind: circle
  center: !point
  r: !float
square:
  kind: square
  corner: !point
  side: !float
shape: !circle | !square
labels: [[[!int, !int], !str], ...]
---
when: !date
data: !blob
tags: !tag-set
origin: !point
shapes: [!shape, ...]
places: !labels
"""

DOC = """when: 2026-11-03
data: aGVsbG8=
tags: [a, b, a]
origin:
  x: 1.5
  y: 2
shapes:
  - kind: circle
    center: {x: 0, y: 0}
    r: 1
  - kind: square
    corner: {x: 2, y: 2}
    side: 3
places:
  - [[1, 2], origin]
  - [[3, 4], target]
"""


class Point:
    def __init__(self, x, y): self.x, self.y = x, y
    def __repr__(self): return f'Point({self.x}, {self.y})'


class Circle:
    def __init__(self, center, r): self.center, self.r = center, r
    def __repr__(self): return f'Circle({self.center}, {self.r})'


class Square:
    def __init__(self, corner, side): self.corner, self.side = corner, side
    def __repr__(self): return f'Square({self.corner}, {self.side})'


BIND = {
    'date': datetime.date.fromisoformat,
    'blob': base64.b64decode,
    'tag-set': set,
    'point': lambda d: Point(d['x'], d['y']),
    'circle': lambda d: Circle(d['center'], d['r']),
    'square': lambda d: Square(d['corner'], d['side']),
    'labels': lambda pairs: {tuple(k): v for k, v in pairs},
}

doc = yaml.load(DOC, Loader=yaml.BaseLoader)
print('unbound:', shadow.Schema(SCHEMA).check(doc))
print('bound:  ', shadow.Schema(SCHEMA, BIND).check(doc))
