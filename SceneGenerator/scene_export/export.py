"""Writes PNG: renders part PNGs through Pixelmator Pro, one part at a time; export_parts.sh runs this.

    python3 -m scene_export.export [part or group ...] [--force PATH ...] [--timeout S] [--dry-run]

A name is a group (an object folder such as left-urn, or "left urn", or leaves), a part's path tail
(left-urn/body), a template id, or a full part path. With no names, every part is rendered.

Pixelmator only opens files it was given access to, so each part SVG in build/parts/ is copied over the one
file it opens, build/pixelmator/import.svg, then opened, exported as a PNG with transparency and closed
without saving. The PNG goes into build/scenes/ by the README's backup and manifest rules; layout and stage copy it from there.
The run stops at the first part that fails, after clearing any Pixelmator alert, and names the part."""

import json
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

from . import BUILD, GENERATOR, INDEX, RENDERED, STAGING, SVG_SCENES, store

SLOT = os.path.join(STAGING, 'import.svg')
RENDERS = os.path.join(BUILD, 'png')
APPLESCRIPT = os.path.join(GENERATOR, 'export_part.applescript')
ALERTS = os.path.join(GENERATOR, 'pixelmator_alerts.sh')


LICENSE = 'https://creativecommons.org/licenses/by-sa/4.0/'
LICENSE_TAGS = {'XMP-cc:AttributionName': 'JamBox', 'XMP-cc:License': LICENSE, 'XMP-dc:Creator': 'JamBox',
                'XMP-dc:Rights': 'Copyright, JamBox, 2026. This work is licensed under the Creative Commons Attribution '
                                 'ShareAlike 4.0 International License. To view a copy of this license, visit '
                                 + LICENSE}


class Stop(Exception):
    pass


def slug(text):
    return '-'.join(text.lower().split())


def select(index, names):
    if not names:
        return list(index)
    chosen = set()
    for name in names:
        n = name.strip('/')
        hits = [p['path'] for p in index
                if p['path'] == n or p['path'].endswith('/' + n)
                or p['path'].split('/')[-2] == slug(n)]
        if not hits:
            raise ValueError('no part or group is called %r' % name)
        chosen.update(hits)
    return [p for p in index if p['path'] in chosen]


def alerts(mode='list'):
    r = subprocess.run([ALERTS] + ([mode] if mode != 'list' else []), capture_output=True, text=True, cwd=GENERATOR)
    if r.returncode != 0:
        raise Stop('pixelmator_alerts.sh %s failed (%d): %s' % (mode, r.returncode, (r.stderr or r.stdout).strip()))
    return r.stdout.strip()


def check_png(path, w, h):
    if not os.path.exists(path):
        return 'Pixelmator wrote no PNG'
    im = Image.open(path)
    if im.size != (w, h):
        return 'the PNG is %d x %d, expected %d x %d' % (im.size + (w, h))
    if im.mode not in ('RGBA', 'RGB'):    # Pixelmator leaves the alpha out of a fully opaque export
        return 'the PNG is %s, not RGBA' % im.mode
    return None


FAINT = 2                        # alpha at or under which Pixelmator writes a pixel's colour as black


def bleed(path):
    """Gives every transparent pixel the colour of the nearest painted one, its alpha staying as it is. Pixelmator
    writes transparent pixels black, and those whose alpha rounds to 1 or 2 too, and the game samples the 2x PNGs
    with linear filtering and blends with straight alpha, so an edge texel blended half with transparent black drew
    a grey fringe round every light shape: a halo round the foam, a dark line under the lip."""
    im = Image.open(path).convert('RGBA')
    px = np.array(im)
    faint = px[..., 3] <= FAINT
    if not faint.any() or faint.all():
        return
    ys, xs = ndimage.distance_transform_edt(faint, return_distances=False, return_indices=True)
    px[..., :3] = px[ys, xs, :3]
    Image.fromarray(px, 'RGBA').save(path)


def licensed(path):
    """Writes the art's license into the PNG's XMP; returns why it couldn't, or None."""
    r = subprocess.run(['exiftool', '-q', '-overwrite_original'] + ['-%s=%s' % kv for kv in LICENSE_TAGS.items()]
                       + [path], capture_output=True, text=True)
    return None if r.returncode == 0 else 'exiftool failed: %s' % (r.stderr or r.stdout).strip()


def same_pixels(a, b):
    if not (os.path.exists(a) and os.path.exists(b)):
        return False
    ia, ib = Image.open(a).convert('RGBA'), Image.open(b).convert('RGBA')
    return ia.size == ib.size and ia.tobytes() == ib.tobytes()


def export_one(part, timeout, st):
    w, h = part['width'], part['height']
    dest = os.path.join(st.root, part['path'] + '@2x.png')
    if st.protected(dest):
        st.skipped.append(st.rel(dest))
        return 'skipped'
    os.makedirs(os.path.dirname(SLOT), exist_ok=True)
    shutil.copyfile(os.path.join(SVG_SCENES, part['svg']), SLOT)
    out = os.path.join(RENDERS, part['path'] + '@2x.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        os.remove(out)
    try:
        r = subprocess.run(['osascript', APPLESCRIPT, SLOT, out, str(w), str(h), str(timeout)],
                           capture_output=True, text=True, timeout=timeout * 3 + 30)
        failure = None if r.returncode == 0 else (r.stderr or r.stdout).strip()
    except subprocess.TimeoutExpired:
        failure = 'osascript did not return within %d s' % (timeout * 3 + 30)
    if failure:
        cleared = alerts('dismiss')
        raise Stop('%s: %s\nPixelmator alerts: %s' % (part['path'], failure, cleared))
    problem = check_png(out, w, h)
    if not problem:
        bleed(out)
        problem = licensed(out)
    if problem:
        raise Stop('%s: %s' % (part['path'], problem))
    if same_pixels(out, dest) and not st.protected(dest):
        os.remove(out)      # Pixelmator's PNG bytes vary between exports of the same image
        st.write(dest, open(dest, 'rb').read())
        return 'unchanged'
    return st.install(out, dest)


def parse(argv):
    names, force, timeout, dry = [], [], 90, False
    it = iter(argv)
    for a in it:
        if a == '--force':
            force.append(next(it))
        elif a == '--timeout':
            timeout = int(next(it))
        elif a == '--dry-run':
            dry = True
        else:
            names.append(a)
    return names, force, timeout, dry


def render(parts, timeout, st):
    """Exports each part's PNG, printing one line per part; returns 1 after the first failure, else 0."""
    done = 0
    try:
        found = alerts()
        if found != 'none':
            raise Stop('Pixelmator is showing an alert, so nothing was opened: %s' % found)
        for p in parts:
            result = export_one(p, timeout, st)
            done += 1
            print('[%d/%d] %-9s scenes/%s@2x.png' % (done, len(parts), result, p['path']), flush=True)
    except Stop as e:
        print('stopped after %d of %d parts: %s' % (done, len(parts), e), file=sys.stderr)
        return 1
    if st.skipped:
        print('skipped (edited since generated; replace with --force <path>):')
        for s in st.skipped:
            print('  scenes/' + s)
    return 0


def main(argv):
    names, force, timeout, dry = parse(argv)
    with open(INDEX) as f:
        index = json.load(f)
    parts = select(index, names)
    if dry:
        for p in parts:
            print(p['path'], p['width'], p['height'])
        return 0
    return render(parts, timeout, store.Store(RENDERED, force=force))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
