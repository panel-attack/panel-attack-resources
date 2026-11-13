"""Writes PNG, into build/previews/compare/: puts a generated piece beside its reference, for matching the art to the painting by eye.

    python3 -m scene_export.compare <concept>/<group>/<piece>.compare.json [--no-generate]

The spec path is relative to the references folder (REFERENCES), unless it is absolute.

The reference JSON names the reference image (`source`, or `image`) and how to get ours:
- `generate`: the module to run first, e.g. "furniture.table_set" or "scene_export render"
- either `svg` + `group`: the SVG the generator writes and the group to render from it, cropped at
  `stage_box`, where the reference image was cut from the stage, or at the stage_box of the JSON
  `stage_box_from` names; or with `"fit": true`, fitted to the reference as a part is
- or `part`: a part path below build/parts/, rendered from build/parts/<part>.svg and fitted to the
  reference: both cropped to their content and ours scaled to the reference's

Each run writes build/previews/compare/<name>/round-NN.png, reference | ours | 50% blend, and round-NN-ours.png."""

import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops

from . import BUILD, GENERATOR, REFERENCES, SHEETS, SVG_SCENES

GAP = 10
ZOOM = 2
SVG_NS = 'http://www.w3.org/2000/svg'
BACKGROUND_TOLERANCE = 40
PART_SCALE = 4         # parts are small: render them big enough to compare with a large reference


def content_box(im):
    """The box of what stands off the image's background: its opaque pixels, or, on an opaque
    image, those far from its corner colour."""
    im = im.convert('RGBA')
    if im.getextrema()[3][0] < 255:
        return im.getchannel('A').point(lambda a: 255 if a > 16 else 0).getbbox()
    rgb = im.convert('RGB')
    r, g, b = ImageChops.difference(rgb, Image.new('RGB', im.size, rgb.getpixel((0, 0)))).split()
    far = ImageChops.lighter(ImageChops.lighter(r, g), b)
    return far.point(lambda v: 255 if v > BACKGROUND_TOLERANCE else 0).getbbox()


def fit(ref, ours):
    """Both cropped to their content, ours scaled to the reference's."""
    r = ref.crop(content_box(ref))
    o = ours.crop(content_box(ours)).resize(r.size, Image.LANCZOS)
    return r, o


def at_stage_box(ref, ours, origin):
    """Ours cropped where the reference was cut from the stage, origin its top left in stage px."""
    x, y = round(origin[0]), round(origin[1])
    return ref, ours.crop((x, y, x + ref.width, y + ref.height))


def on(colour, im):
    im = im.convert('RGBA')
    bg = Image.new('RGBA', im.size, colour)
    bg.alpha_composite(im)
    return bg.convert('RGB')


def sheet(ref, ours, zoom=ZOOM):
    """Reference | ours | their 50% blend, each scaled by zoom."""
    ref, ours = ref.convert('RGB'), ours.convert('RGB')
    w, h = ref.width * zoom, ref.height * zoom
    out = Image.new('RGB', (3 * w + 2 * GAP, h), 'white')
    out.paste(ref.resize((w, h), Image.LANCZOS), (0, 0))
    out.paste(ours.resize((w, h), Image.LANCZOS), (w + GAP, 0))
    out.paste(Image.blend(ref, ours, 0.5).resize((w, h), Image.LANCZOS), (2 * (w + GAP), 0))
    return out


def next_round(folder):
    found = [int(m.group(1)) for f in os.listdir(folder) for m in [re.fullmatch(r'round-(\d+)\.png', f)] if m]
    return max(found, default=0) + 1


def render_svg(path, scale=1):
    """The SVG as an RGBA image `scale` times its size, through Quick Look like Finder's preview. Quick Look
    draws a square thumbnail, so the SVG is squared off first and the image cut back to its own size."""
    ET.register_namespace('', SVG_NS)
    root = ET.parse(path).getroot()
    w, h = (float(root.get(k).rstrip('px')) for k in ('width', 'height'))
    side = max(w, h)
    root.set('width', '%g' % side)
    root.set('height', '%g' % side)
    root.set('viewBox', '0 0 %g %g' % (side, side))
    tmp = tempfile.mkdtemp()
    square = os.path.join(tmp, os.path.basename(path))
    ET.ElementTree(root).write(square)
    subprocess.run(['qlmanage', '-t', '-s', str(round(side * scale)), '-o', tmp, square], capture_output=True, check=True)
    im = Image.open(square + '.png').convert('RGBA')
    return im.crop((0, 0, round(w * scale), round(h * scale)))


def svg_group(svg, group):
    """A copy of svg keeping only the group with that id (and the defs), written to a temp file."""
    ET.register_namespace('', SVG_NS)
    root = ET.parse(svg).getroot()
    keep = set()
    for g in root.iter('{%s}g' % SVG_NS):
        if g.get('id') == group:
            keep |= set(map(id, g.iter()))

    def prune(el):
        for ch in list(el):
            if ch.tag.endswith('defs') or id(ch) in keep:
                continue
            if any(id(e) in keep for e in ch.iter()):
                prune(ch)
            else:
                el.remove(ch)
    prune(root)
    path = os.path.join(tempfile.mkdtemp(), group + '.svg')
    ET.ElementTree(root).write(path)
    return path


def ours_for(spec):
    if 'part' in spec:
        return render_svg(os.path.join(SVG_SCENES, spec['part'] + '.svg'), PART_SCALE)
    return render_svg(svg_group(os.path.join(SHEETS, spec['svg']), spec['group']))


def framed(spec, ref, ours, folder):
    """The reference and ours framed alike, and the background to lay them on."""
    if 'part' in spec or spec.get('fit'):
        ref, ours = fit(ref, ours)
        return ref, ours, ref.getpixel((0, 0))
    box = spec.get('stage_box') or json.load(open(os.path.join(folder, spec['stage_box_from'])))['stage_box']
    ref, ours = at_stage_box(ref, ours, box[:2])
    return ref, ours, (255, 255, 255, 255)


def main(argv):
    ref_json = os.path.join(REFERENCES, argv[0])
    spec = json.load(open(ref_json))
    folder = os.path.dirname(os.path.abspath(ref_json))
    if spec.get('generate') and '--no-generate' not in argv:
        subprocess.run([sys.executable, '-m'] + spec['generate'].split(), cwd=GENERATOR, check=True, capture_output=True)
    ref = Image.open(os.path.join(folder, spec.get('image', spec.get('source')))).convert('RGBA')
    ref, ours, background = framed(spec, ref, ours_for(spec), folder)
    if background[3] < 255:
        background = (255, 255, 255, 255)
    out_dir = os.path.join(BUILD, 'previews', 'compare', spec['name'])
    os.makedirs(out_dir, exist_ok=True)
    n = next_round(out_dir)
    ours_flat = on(background, ours)
    sheet(on(background, ref), ours_flat).save(os.path.join(out_dir, 'round-%02d.png' % n))
    ours_flat.save(os.path.join(out_dir, 'round-%02d-ours.png' % n))
    print(os.path.join(out_dir, 'round-%02d.png' % n))


if __name__ == '__main__':
    main(sys.argv[1:])
