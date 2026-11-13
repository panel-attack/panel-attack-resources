"""python3 -m scene_export render [part or group ...] [--all] [--force PATH ...] [--timeout S]
python3 -m scene_export layout [file ...]

render writes SVG and PNG, never JSON. It runs every IMAGE_MODULES generator that draws a sheet into build/sheets/, writes each
module's part SVGs into build/parts/ at their PNG's path (with build/index.json listing them),
then renders through Pixelmator Pro the PNGs into the game theme's scenes/: the named parts, or every part with
--all, else the parts whose SVG changed or whose PNG is missing. It never touches the scene JSON. --force paths
are PNGs below the theme's scenes/ to replace though they were edited.

layout writes JSON, never SVG or PNG: each JSON_MODULES generator's file into the game theme's scenes/, or only
the named files. Run it to make a file once; after that the file is edited in the scene editor or by hand. A
file whose bytes differ from the new output is moved to build/.backup/ first."""

import importlib
import json
import os
import subprocess
import sys

from . import GAME_SCENES, GENERATOR, INDEX, SVG_SCENES, export, layout, store, svgtools

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
        problems = svgtools.validate(p.svg)
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


def layout_modules(modules, names):
    """The modules writing the named files, or all of them."""
    files = {m.OUTPUT: m for m in modules}
    unknown = [n for n in names if n not in files]
    if unknown:
        raise SystemExit('layout makes no %s; it makes %s' % (', '.join(unknown), ', '.join(sorted(files))))
    return [m for rel, m in files.items() if not names or rel in names]


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
    parts = [p for m in modules for p in m.parts()]
    changed = write_build(parts, SVG_SCENES, INDEX)
    print('%d part SVGs in %s, %d changed' % (len(parts), SVG_SCENES, len(changed)))
    with open(INDEX) as f:
        index = json.load(f)
    chosen = to_render(index, names, every, changed,
                       lambda path: os.path.exists(os.path.join(GAME_SCENES, path + '@2x.png')))
    if not chosen:
        print('no PNGs to render')
        return 0
    return export.render(chosen, timeout, store.Store(GAME_SCENES, force=force, state=GENERATOR))


def write_layout(names):
    st = store.Store(GAME_SCENES, state=GENERATOR)
    for m in layout_modules([importlib.import_module(m) for m in JSON_MODULES], names):
        layout.write(m.OUTPUT, m.build(), st)
    return 0


def main(argv):
    if argv[:1] == ['render']:
        return render(argv[1:])
    if argv[:1] == ['layout']:
        return write_layout(argv[1:])
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
