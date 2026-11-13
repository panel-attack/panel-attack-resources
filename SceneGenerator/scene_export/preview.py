"""Writes PNG: composites a scene JSON the way the panel-game AnimationLoader draws it, to check the scene without the game.

    python3 -m scene_export.preview <scene.json> <out.png> [--root <theme folder>]

Refs resolve like the loader's (file part relative to the root like image paths, ids looked up across every
file read, overrides applied recursively). Each node's transform is translate(position - anchor offset),
then translate(pivot), rotate, scale, translate(-pivot), in scene units; @2x images are half their pixel
size in units. The scene draws in document order, parents before their children. The output is at 2x (1536 x 1024 for EsmeTerrace)."""

import copy
import json
import math
import os
import sys

import numpy as np
from PIL import Image

ANCHORS = {'topLeft': (0, 0), 'topCenter': (.5, 0), 'topRight': (1, 0), 'centerLeft': (0, .5),
           'center': (.5, .5), 'centerRight': (1, .5), 'bottomLeft': (0, 1), 'bottomCenter': (.5, 1),
           'bottomRight': (1, 1)}


def mul(m, n):
    a, b, c, d, e, f = m
    a2, b2, c2, d2, e2, f2 = n
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2, a * e2 + c * f2 + e,
            b * e2 + d * f2 + f)


def translate(x, y):
    return (1, 0, 0, 1, x, y)


def apply(m, x, y):
    a, b, c, d, e, f = m
    return a * x + c * y + e, b * x + d * y + f


def offset(name, w, h):
    fx, fy = ANCHORS.get(name, (0, 0))
    return fx * w, fy * h


def node_matrix(node, w, h, has_texture=True):
    """The node's own transform; w, h are its image size in units."""
    pos = node.get('position') or {}
    ax, ay = offset(node.get('anchor', 'topLeft'), w, h)
    pivot = node.get('pivot') or ('center' if has_texture else 'topLeft')
    px, py = offset(pivot, w, h)
    r = node.get('rotation', 0)
    c, s = math.cos(r), math.sin(r)
    sx, sy = node.get('xScale', 1), node.get('yScale', 1)
    m = translate(pos.get('x', 0) - ax + px, pos.get('y', 0) - ay + py)
    m = mul(m, (c, s, -s, c, 0, 0))
    m = mul(m, (sx, 0, 0, sy, 0, 0))
    return mul(m, translate(-px, -py))


# ---------------------------------------------------------------- loading like the loader

def merge(target, overrides):
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(target.get(k), dict):
            merge(target[k], v)
        elif isinstance(v, list) and isinstance(target.get(k), list):
            for i, item in enumerate(v):
                if i < len(target[k]) and isinstance(item, dict) and isinstance(target[k][i], dict):
                    merge(target[k][i], item)
                elif i < len(target[k]):
                    target[k][i] = copy.deepcopy(item)
                else:
                    target[k].append(copy.deepcopy(item))
        else:
            target[k] = copy.deepcopy(v)


class Scene:
    def __init__(self, path, root):
        self.root = root
        self.files = {}
        self.ids = {}
        self.images = {}
        self.read(os.path.normpath(path))
        self.doc = copy.deepcopy(self.files[os.path.normpath(path)])
        for n in self.doc['drawables']:
            self.resolve(n, os.path.normpath(path))

    def read(self, path):
        if path in self.files:
            return
        with open(path) as f:
            doc = json.load(f)
        self.files[path] = doc
        for n in doc.get('drawables', []):
            self.index(n)

    def index(self, node):
        ref = node.get('ref')
        if ref and '.json' in ref:
            self.read(os.path.normpath(os.path.join(self.root, ref.split('#')[0])))
        if 'id' in node:
            if node['id'] in self.ids:
                raise ValueError('Duplicate id detected: %s' % node['id'])
            self.ids[node['id']] = node
        for ch in node.get('children', []):
            self.index(ch)

    def resolve(self, node, path):
        ref = node.get('ref')
        if ref:
            if ref.endswith('.json'):
                raise ValueError('whole-file imports are not used by this scene')
            rid = ref.split('#', 1)[1] if '#' in ref else ref
            extra = set(node) - {'id', 'ref', 'overrides', 'templateOnly'}
            if extra:
                raise ValueError('Reference has unexpected keys %s' % sorted(extra))
            if rid not in self.ids:
                raise ValueError('Unknown ref: %s' % rid)
            src = copy.deepcopy(self.ids[rid])
            merge(src, node.get('overrides') or {})
            src['id'] = node.get('id')
            src.pop('templateOnly', None)
            node.clear()
            node.update(src)
        for ch in node.get('children', []):
            self.resolve(ch, path)

    def image(self, file_path):
        if file_path not in self.images:
            im = Image.open(os.path.join(self.root, file_path + '@2x.png')).convert('RGBA')
            if im.width % 2 or im.height % 2:
                raise ValueError('%s@2x.png is %d x %d; the loader needs even sizes' % (file_path, *im.size))
            self.images[file_path] = im.convert('RGBa')
        return self.images[file_path]


# ---------------------------------------------------------------- drawing

def draw(canvas, image, m):
    """Draws a premultiplied image whose pixels are half units through unit matrix m onto the 2x canvas."""
    to_px = mul(mul((2, 0, 0, 2, 0, 0), m), (.5, 0, 0, .5, 0, 0))
    w, h = image.size
    corners = [apply(to_px, x, y) for x, y in ((0, 0), (w, 0), (0, h), (w, h))]
    x0 = max(int(math.floor(min(c[0] for c in corners))) - 1, 0)
    y0 = max(int(math.floor(min(c[1] for c in corners))) - 1, 0)
    x1 = min(int(math.ceil(max(c[0] for c in corners))) + 1, canvas.shape[1])
    y1 = min(int(math.ceil(max(c[1] for c in corners))) + 1, canvas.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    a, b, c, d, e, f = mul(to_px, (1, 0, 0, 1, 0, 0))
    det = a * d - b * c
    ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
    ie, if_ = -(ia * e + ic * f), -(ib * e + id_ * f)
    # PIL wants output -> input, for output pixel centres; shift by the crop origin
    coeffs = (ia, ic, ia * x0 + ic * y0 + ie, ib, id_, ib * x0 + id_ * y0 + if_)
    warped = image.transform((x1 - x0, y1 - y0), Image.AFFINE, coeffs, resample=Image.BILINEAR)
    src = np.asarray(warped, dtype=np.float32) / 255.0
    dst = canvas[y0:y1, x0:x1]
    dst[:] = src + dst * (1.0 - src[..., 3:4])


def render_nodes(scene, canvas, nodes, parent_m):
    for n in nodes:
        if n.get('templateOnly'):
            continue
        fp = n.get('filePath')
        if fp:
            im = scene.image(fp)
            w, h = im.width / 2, im.height / 2
        else:
            w = h = 0
        m = mul(parent_m, node_matrix(n, w, h, bool(fp)))
        if fp and n.get('alpha', 1) > 0:
            draw(canvas, im, m)
        render_nodes(scene, canvas, n.get('children', []), m)


def render(scene_path, root=None, size=(1536, 1024)):
    root = root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(scene_path))))
    scene = Scene(scene_path, root)
    canvas = np.zeros((size[1], size[0], 4), np.float32)
    render_nodes(scene, canvas, scene.doc['drawables'], (1, 0, 0, 1, 0, 0))
    alpha = canvas[..., 3:4]
    rgb = np.where(alpha > 1e-6, canvas[..., :3] / np.maximum(alpha, 1e-6), 0)
    out = np.dstack([rgb, alpha]) * 255.0
    return Image.fromarray(np.clip(np.round(out), 0, 255).astype(np.uint8), 'RGBA')


def main(argv):
    if len(argv) < 2:
        print(__doc__.split('\n\n')[1])
        return 2
    root = None
    if '--root' in argv:
        i = argv.index('--root')
        root = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    render(argv[0], root).save(argv[1])
    print('wrote', argv[1])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
