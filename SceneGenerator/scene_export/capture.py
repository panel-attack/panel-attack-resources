"""Library, writes nothing: runs planters.py's and bushes.py's builders with foliage.py's leaf, flower, rose, bud and
twig calls recorded, so every foliage piece in planters.svg and bushes.svg can be traced back to the arguments
that drew it."""

import contextlib
import random
from dataclasses import dataclass, field

from . import GENERATOR  # noqa: F401  (puts the art generators on sys.path)
from plants import bushes, foliage
from furniture import planters


@dataclass
class Foliage:
    """One leaf, flower, rose or bud as foliage.py drew it. names are the ids of every path it drew."""
    kind: str
    name: str
    params: dict
    names: list = field(default_factory=list)


@contextlib.contextmanager
def recording():
    """Patches foliage's drawing functions; yields the dict of records by name (the last call wins, as
    planters.py redraws a vine while fitting it)."""
    records = {}
    saved = {k: getattr(foliage, k) for k in ('leaf', 'flower', 'rose', 'bud', 'twig')}

    def leaf(name, base, angle, length, tone='leaf-light', bend=None, rng=None, width=foliage.LEAF_WIDTH,
             stroke=foliage.LEAF_STROKE, gloss=None, shade=None):
        rng = rng or random.Random(0)
        # resolve the random choices exactly as foliage.leaf would, in the same order
        if bend is None:
            bend = rng.uniform(-foliage.LEAF_BEND, foliage.LEAF_BEND)
        if gloss is None:
            gloss = rng.random() < foliage.GLOSS_CHANCE
        shade = shade or foliage.LEAF_SHADE[tone]
        shapes = saved['leaf'](name, base, angle, length, tone, bend=bend, rng=rng, width=width, stroke=stroke,
                               gloss=gloss, shade=shade)
        records[name] = Foliage('leaf', name, dict(base=tuple(base), angle=angle, length=length, tone=tone,
                                                   bend=bend, width=width, stroke=stroke, gloss=bool(gloss),
                                                   shade=shade), [s.name for s in shapes])
        return shapes

    def flower(name, c, radius, rot=0.0, squash=1.0, white=False, stroke=foliage.STROKE,
               notch=foliage.PETAL_NOTCH):
        shapes = saved['flower'](name, c, radius, rot, squash, white, stroke, notch)
        records[name] = Foliage('flower', name, dict(c=tuple(c), radius=radius, rot=rot, squash=squash,
                                                     white=bool(white), stroke=stroke, notch=notch),
                                [s.name for s in shapes])
        return shapes

    def rose(name, c, radius, rot=0.0, squash=1.0, stroke=foliage.STROKE):
        shapes = saved['rose'](name, c, radius, rot, squash, stroke)
        records[name] = Foliage('rose', name, dict(c=tuple(c), radius=radius, rot=rot, squash=squash,
                                                   stroke=stroke), [s.name for s in shapes])
        return shapes

    def bud(name, base, angle, length, stroke=foliage.STROKE):
        shapes = saved['bud'](name, base, angle, length, stroke)
        records[name] = Foliage('bud', name, dict(base=tuple(base), angle=angle, length=length, stroke=stroke),
                                [s.name for s in shapes])
        return shapes

    def twig(name, base, angle, length, width):
        shapes = saved['twig'](name, base, angle, length, width)
        records[name] = Foliage('twig', name, dict(base=tuple(base), angle=angle, length=length, width=width),
                                [s.name for s in shapes])
        return shapes

    for k, f in (('leaf', leaf), ('flower', flower), ('rose', rose), ('bud', bud), ('twig', twig)):
        setattr(foliage, k, f)
    try:
        yield records
    finally:
        for k, f in saved.items():
            setattr(foliage, k, f)


def build_planters():
    """The foliage records of planters.svg, drawn as planters.main draws it."""
    with recording() as records:
        out = planters.Out()
        planters.urn(out, planters.SCENE, 'Right urn', 41)
        planters.crystal_planter(out, planters.SCENE)
        planters.urn(out, planters.SCENE, 'Left urn', 31)
    return records


def build_bush():
    """The foliage records of bushes.svg, drawn as bushes.main draws it."""
    with recording() as records:
        bushes.corner_bush(planters.Out())
    return records
