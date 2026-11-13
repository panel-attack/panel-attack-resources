"""Library, writes a stage folder: a scene as the game loads a stage, its background.json one canvas container
holding the scene, beside the template files it draws, holding only the templates it draws, and their PNGs. The
theme's files are picked the same way, from the main menu."""

import os
import shutil

from . import game


def used_templates(docs, scene):
    """{file: set of template ids, or None for the whole file} the scene draws, through templates that draw others."""
    used, todo = {}, list(docs[scene]['drawables'])
    while todo:
        n = todo.pop()
        todo += n.get('children', [])
        if 'ref' not in n:
            continue
        file, _, tid = n['ref'].partition('#')
        ids = used.setdefault(file, set())
        if not tid:
            if ids is not None:
                used[file] = None
                todo += docs[file]['drawables']
        elif ids is not None and tid not in ids:
            ids.add(tid)
            todo.append(next(t for t in docs[file]['drawables'] if t['id'] == tid))
    return used


def drawn(docs, root):
    """{file: doc} of the files root draws, each holding only the templates it draws."""
    return {file: {**docs[file], 'drawables': [t for t in docs[file]['drawables'] if ids is None or t['id'] in ids]}
            for file, ids in sorted(used_templates(docs, root).items())}


def files(docs, scene):
    """{path in the stage folder: doc}."""
    out = {'background.json': game.theme_file(game.canvas(docs[scene]['drawables']), None)}
    out.update({file: game.theme_file(doc, None) for file, doc in drawn(docs, scene).items()})
    return out


def theme(docs, root):
    """{path below the theme's scenes/: doc} of root and the files it draws, as the theme holds them."""
    out = {root: game.theme_file(docs[root])}
    out.update({file: game.theme_file(doc) for file, doc in drawn(docs, root).items()})
    return out


def images(stage_files):
    return sorted({n['filePath'] for doc in stage_files.values() for n in game.walk(doc['drawables'])
                   if 'filePath' in n})


def write(docs, scene, out, pngs):
    """The scene as a stage into out, its PNGs copied from pngs; refused, writing nothing, if its root isn't one
    canvas container or a PNG it draws is missing."""
    stage_files = files(docs, scene)
    game.check_root(stage_files['background.json'], scene)
    missing = [p for p in images(stage_files) if not os.path.exists(os.path.join(pngs, p + '@2x.png'))]
    if missing:
        raise SystemExit('%s: no PNG for %s' % (scene, ', '.join(missing)))
    for rel, doc in stage_files.items():
        os.makedirs(os.path.dirname(os.path.join(out, rel)), exist_ok=True)
        with open(os.path.join(out, rel), 'wb') as f:
            f.write(game.to_json(doc))
    for p in images(stage_files):
        os.makedirs(os.path.dirname(os.path.join(out, p)), exist_ok=True)
        shutil.copyfile(os.path.join(pngs, p + '@2x.png'), os.path.join(out, p + '@2x.png'))
