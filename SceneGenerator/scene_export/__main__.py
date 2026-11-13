"""python3 -m scene_export render [part or group ...] [--all] [--force PATH ...] [--timeout S]
python3 -m scene_export layout [file ...]
python3 -m scene_export stage <scene file> <stage folder> [--pngs FOLDER]

render writes SVG and PNG, never JSON. It runs every IMAGE_MODULES generator that draws a sheet into build/sheets/, writes each
module's part SVGs, drawn at their native size (native.py), into build/parts/ at their PNG's
path (with build/index.json listing them),
then renders through Pixelmator Pro the PNGs into build/scenes/: the named parts, or every part with --all, else
the parts whose SVG changed or whose PNG is missing. It never touches the scene JSON. --force paths are PNGs below
build/scenes/ to replace though they were edited.

layout writes JSON and copies PNG: the main menu's file and the files it draws, holding only the templates it
draws, into the game theme's scenes/, or only the named ones among them, with the PNGs from build/scenes/ they
draw. Scenes the main menu doesn't draw stay out of the theme. A file whose bytes differ from the new output is
moved to build/.backup/ first, and a PNG edited since layout copied it is left alone.

stage writes the scene file, as layout makes it, as a stage folder (stage.py): background.json one canvas container
holding the scene, the template files it draws, and their PNGs, copied from build/scenes/ or --pngs."""

import importlib
import json
import os
import subprocess
import sys

from . import GENERATOR, INDEX, RENDERED, SVG_SCENES, export, layout, native, stage, store, svgtools

# each makes the parts in the parts/ folder beside it; one with a main() draws the sheet SVG beside itself first
IMAGE_MODULES = ['scenery.sky', 'scenery.clouds', 'scenery.landscape', 'structures.houses', 'plants.trees',
                 'plants.leaves', 'plants.flowers', 'plants.roses', 'plants.stems', 'plants.bushes',
                 'furniture.planters', 'furniture.table_set', 'EsmeTerrace.background', 'EsmeTerrace.floor',
                 'EsmeTerrace.rail', 'EsmeTerrace.shadows', 'scenery.sun', 'scenery.alps', 'scenery.valley',
                 'plants.broadleaf', 'plants.pines', 'plants.wildflowers', 'structures.windmill', 'structures.airship',
                 'structures.train', 'scenery.mesa', 'scenery.spring_peaks', 'scenery.spring_valley', 'plants.blossom',
                 'plants.lantern_tree', 'plants.meadow_flowers']
# each builds the one file below the game's scenes/ its OUTPUT names
JSON_MODULES = ['scenery.sky_template', 'scenery.clouds_template', 'scenery.landscape_template',
                'structures.houses_template', 'plants.trees_template', 'plants.leaves_template',
                'plants.flowers_template', 'plants.roses_template', 'plants.stems_template', 'plants.branches_template',
                'plants.bushes_template', 'furniture.planters_template', 'furniture.table_set_template',
                'EsmeTerrace.EsmeTerrace', 'scenery.sun_template', 'scenery.alps_template',
                'scenery.valley_template', 'plants.broadleaf_template', 'plants.pines_template',
                'plants.wildflowers_template',
                'structures.windmill_template', 'structures.airship_template', 'DayValley.DayValley',
                'structures.train_template', 'scenery.mesa_template', 'scenery.spring_peaks_template',
                'scenery.spring_valley_template', 'plants.blossom_template', 'plants.lantern_tree_template',
                'plants.meadow_flowers_template', 'TrainMeadow.TrainMeadow', 'MainMenu']


def indexed_svgs(root, index):
    if not os.path.exists(index):
        return set()
    with open(index) as f:
        return {os.path.join(root, p['svg']) for p in json.load(f)}


def write_build(parts, root, index):
    """Each part's SVG at root/<part path>.svg, and the index of them; SVGs the last index listed that
    this one doesn't are removed, and no others. Returns the paths of the parts whose SVG changed."""
    keep, changed = set(), []
    for p in parts:
        problems = svgtools.validate(p.svg, p.strip, native=True)
        if problems:
            raise SystemExit('%s: %s' % (p.path, '; '.join(problems)))
        path = os.path.join(root, p.path + '.svg')
        keep.add(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        old = open(path).read() if os.path.exists(path) else None
        if old != p.svg:
            with open(path, 'w') as f:
                f.write(p.svg)
            changed.append(p.path)
    for path in indexed_svgs(root, index) - keep:
        if os.path.exists(path):
            os.remove(path)
    os.makedirs(os.path.dirname(index), exist_ok=True)
    with open(index, 'w') as f:
        json.dump([{'path': p.path, 'svg': p.path + '.svg', 'width': p.box[2], 'height': p.box[3]} for p in parts],
                  f, indent=1)
        f.write('\n')
    return changed


def to_render(index, names, every, changed, has_png):
    if every:
        return list(index)
    if names:
        return export.select(index, names)
    return [p for p in index if p['path'] in changed or not has_png(p['path'])]


def parse(argv):
    names, force, timeout, every = [], [], 90, False
    it = iter(argv)
    for a in it:
        if a == '--force':
            force.append(next(it))
        elif a == '--timeout':
            timeout = int(next(it))
        elif a == '--all':
            every = True
        else:
            names.append(a)
    return names, force, timeout, every


def draw_sheets():
    """Runs every IMAGE_MODULES generator that draws a sheet, into build/sheets/; returns the modules."""
    modules = [importlib.import_module(m) for m in IMAGE_MODULES]
    for m in modules:
        if hasattr(m, 'main'):
            r = subprocess.run([sys.executable, '-m', m.__name__], cwd=GENERATOR, capture_output=True, text=True)
            if r.returncode != 0:
                raise SystemExit('%s failed:\n%s' % (m.__name__, r.stderr or r.stdout))
    return modules


def render(argv):
    names, force, timeout, every = parse(argv)
    modules = draw_sheets()
    _, _, resolutions, anchors = layout.planned()
    parts = [native.native_part(p, resolutions.get(p.path, (1, 1)), anchors.get(p.path, 'topLeft'))
             for m in modules for p in m.parts()]
    changed = write_build(parts, SVG_SCENES, INDEX)
    print('%d part SVGs in %s, %d changed' % (len(parts), SVG_SCENES, len(changed)))
    with open(INDEX) as f:
        index = json.load(f)
    chosen = to_render(index, names, every, changed,
                       lambda path: os.path.exists(os.path.join(RENDERED, path + '@2x.png')))
    if not chosen:
        print('no PNGs to render')
        return 0
    return export.render(chosen, timeout, store.Store(RENDERED, force=force))


def write_layout(names):
    layout.write(*names)
    return 0


def write_stage(argv):
    pngs = RENDERED
    if '--pngs' in argv:
        i = argv.index('--pngs')
        pngs, argv = argv[i + 1], argv[:i] + argv[i + 2:]
    if len(argv) != 2:
        raise SystemExit(__doc__)
    scene, out = argv
    if scene not in layout.SCENES:
        raise SystemExit('stage makes no %s; it makes %s' % (scene, ', '.join(layout.SCENES)))
    _, docs, _, _ = layout.planned()
    stage.write(docs, scene, out, pngs)
    print('stage    %s from %s' % (out, scene))
    return 0


def main(argv):
    if argv[:1] == ['render']:
        return render(argv[1:])
    if argv[:1] == ['layout']:
        return write_layout(argv[1:])
    if argv[:1] == ['stage']:
        return write_stage(argv[1:])
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
