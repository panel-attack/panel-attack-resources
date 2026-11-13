"""Library, writes the game theme's scenes/ folder: the main menu's file, the files it draws, holding only the
templates it draws, and the rendered PNGs they draw; scenes the main menu doesn't draw stay out of the theme. Every
file is laid out with all the others, since how the scenes draw a part sets the size its PNG is drawn at
(native.py). A file whose bytes differ from the new output is moved to build/.backup/ first."""

import functools
import importlib
import os

from . import BUILD, GAME_SCENES, RENDERED, game, native, required, stage, store

SCENES = ['EsmeTerrace/EsmeTerrace.json', 'DayValley/DayValley.json', 'TrainMeadow/TrainMeadow.json']
THEME_ROOT = 'MainMenu.json'


def finished(docs, scenes, sheet_px):
    """(docs, resolutions): the docs as generators build them, each part's scales divided by the resolution its PNG
    is drawn at and each part used once put on a whole canvas unit; refused if a part used once is still drawn
    scaled or off a whole unit. sheet_px is {image: its (w, h) in sheet px}."""
    at_sheet_size = {image: (native.native_px(w) / 2, native.native_px(h) / 2) for image, (w, h) in sheet_px.items()}
    docs, rs = native.resolved(docs, scenes, at_sheet_size)

    def size_of(image):
        (w, h), (rx, ry) = sheet_px[image], rs.get(image, (1, 1))
        return native.native_px(w, rx) / 2, native.native_px(h, ry) / 2
    docs = native.aligned(docs, scenes, size_of)
    native.check(docs, scenes, size_of)
    return docs, rs


def anchors(docs):
    """{image: the anchor its nodes draw it from}."""
    return {native.without_folder(n['filePath']): n.get('anchor', 'topLeft')
            for doc in docs.values() for n in native.walk(doc['drawables']) if 'filePath' in n}


@functools.cache
def planned():
    """(modules by file, docs, resolutions, anchors) of every JSON generator's file, laid out together."""
    from .__main__ import IMAGE_MODULES, JSON_MODULES
    modules = {m.OUTPUT: m for m in map(importlib.import_module, JSON_MODULES)}
    sheet_px = {p.path: p.size for m in IMAGE_MODULES for p in importlib.import_module(m).parts()}
    built = {rel: m.build() for rel, m in modules.items()}
    docs, rs = finished(built, SCENES, sheet_px)
    return modules, docs, rs, anchors(built)


def write_docs(docs, names, st=None, roots=()):
    """The named docs, as the theme holds them, into scenes/<name>; prints what became of each file. Every root
    file among them is checked to be one canvas container first, and nothing is written if one isn't."""
    st = st or store.Store(required(GAME_SCENES, 'SCENE_GAME_THEME'), state=BUILD)
    for rel in names:
        if rel in roots:
            game.check_root(docs[rel], rel)
    for rel in names:
        print('%-9s scenes/%s' % (st.replace(os.path.join(st.root, rel), game.to_json(docs[rel])), rel))


def write_theme(docs, root, st, pngs, names=()):
    """root's theme files, or the named ones among them, into st's folder, and the PNGs from pngs they draw; a PNG
    edited since the generator wrote it is left alone. Refused, writing nothing, for a name root doesn't draw."""
    theme = stage.theme(docs, root)
    unknown = [n for n in names if n not in theme]
    if unknown:
        raise SystemExit('the theme has no %s; %s draws %s' % (', '.join(unknown), root, ', '.join(sorted(theme))))
    chosen = {rel: theme[rel] for rel in (names or theme)}
    write_docs(chosen, list(chosen), st, [root])
    for image in stage.images(chosen):
        rel = image.partition('/')[2] + '@2x.png'
        with open(os.path.join(pngs, rel), 'rb') as f:
            print('%-9s scenes/%s' % (st.write(os.path.join(st.root, rel), f.read()), rel))


def write(*names, st=None):
    """The named theme files, or every one, into the theme's scenes/, with the PNGs they draw."""
    _, docs, _, _ = planned()
    write_theme(docs, THEME_ROOT, st or store.Store(required(GAME_SCENES, 'SCENE_GAME_THEME'), state=BUILD), RENDERED, names)
