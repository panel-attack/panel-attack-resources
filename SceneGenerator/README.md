# Scene generator

Generates the scene layouts for the panel-game animation loader (`docs/animations.md` there) and the
images they draw. A scene is one JSON file in the loader's format.

## Where things go

```
panel-attack-resources/
  SceneGenerator/               this generator
    common/, scene_export/      shared helpers and the render and layout commands
    plants/, furniture/,        the generators, grouped as the game's scenes/ folders are
    structures/, scenery/,
    EsmeTerrace/
    build/                      everything the generator makes, none of it committed: sheets/, each
                                generator's sheet SVG at its path; parts/, the part SVGs cut from them;
                                scenes/, every rendered PNG; .manifest.json, .backup/, previews/, and
                                pixelmator/, the one file Pixelmator opens

panel-attack-references/        reference images (each folder's painting is source.png), by the same folders

<game worktree>/client/assets/themes/Panel Attack Modern/
  scenes/                       what the main menu draws, and nothing else
    MainMenu.json               places the train meadow on the main menu's canvas
    TrainMeadow/TrainMeadow.json  the scene: where everything is placed
    plants/, scenery/, structures/  the template files it draws, holding only the templates it draws
      parts/<group>/<name>@2x.png

<game worktree>/client/assets/default_data/stages/Esme Terrace/
  background.json               the terrace scene as a stage, written by stage
  EsmeTerrace/, plants/, ...    the template files and PNGs it draws
```

Each image or JSON file has its own generator. A drawing generator `X.py` writes its sheet `X.svg` into
`build/sheets/` at its own path, and `X_flat.svg` when it starts from a flat drawing; `render` cuts the part SVGs out of the sheets.
`X_template.py` writes the game's `X.json`, the templates drawing those parts. A scene's generator is named
for the scene (`EsmeTerrace/EsmeTerrace.py`) and only places what the others make. What a generator
measures off a reference is in `<thing>_reference.py` beside it. "Template" only ever means a templateOnly
drawable in the game's JSON.

`SCENE_GAME_THEME` names the theme folder the scenes go into, `<game worktree>/client/assets/themes/Panel
Attack Modern`, and `SCENE_REFERENCES` the references folder. Writing into the theme stops without the
first, and the tests that read the references are skipped without the second. A fresh checkout has no
sheets, so the tests draw them first.

A concept folder holds one file of templates per kind of thing, and the images they draw under its
`parts/`. A scene's own folder holds only the scene file and what is drawn for that scene's camera
alone: its floor, rail, shadows, near woods and the lake below the rail. Everything else is a
template a scene places by `ref`. Every image path (`filePath`) is relative to the theme folder, as the
game resolves it, without extension and without `@2x`, e.g. `scenes/plants/parts/leaves/leaf-urn-mid-arch`.
The scene editor and `preview` take the theme folder as their root by default, so they resolve them the same way.

## Who owns what

The generators own the art: each part's SVG and its PNG. To change a part, change its generator and
render. A part SVG edited in Pixelmator is overwritten by the next render, so an edit made there has to
be carried into the generator first.

The scene JSON, the templates and the scenes placing them, is made once by `layout` and from then on
edited in the scene editor or by hand. Rendering never touches it, so when a change to a generator moves
or resizes a part's crop, the placements of that part in the JSON are for whoever made the change to fix.

```bash
python3 -m scene_export render                  # every drawing generator, then the PNGs whose SVG changed
python3 -m scene_export render table-set        # ... and those parts' PNGs though unchanged
python3 -m scene_export render --all            # ... and every PNG
./export_parts.sh table                         # only the PNG, from the SVG already in build/parts/
python3 -m scene_export layout plants/branches.json   # make a JSON file again
python3 -m scene_export stage EsmeTerrace/EsmeTerrace.json <folder>   # the scene as a stage folder
```

`render` puts every PNG in `build/scenes/`; `layout` and `stage` copy the ones they draw from there, so a
scene the main menu doesn't draw, such as the terrace, never lands in the theme.

`stage` writes `background.json`, the canvas container holding the scene, beside only the template files and
templates the scene draws and their PNGs, with paths from the stage folder.

`layout` with no names writes `MainMenu.json` and every file it draws, holding only the templates it draws, and
copies their PNGs. A file whose bytes differ from the new output is moved to the backups first, so writing over
an edited file can be undone from there.

Scenes are laid out in the game's canvas units: the canvas is 1280 x 720 units, 2560 x 1440 px at 2x. The
sheets are drawn in 1536 x 1024 px; cutting maps a sheet px to 5/6 of a unit and cuts as much off the top
of the drawing as off the bottom, and that mapping is in `scene_export/cutting.py` alone. Only `@2x` images
exist, and each PNG is exported at twice the size the scenes typically draw it (`scene_export/native.py`):
a part used once at exactly the size it is drawn, upright and still on a whole unit, so the game draws it
pixel for pixel; a part used at several scales at the largest of them, so it is only ever shrunk. `layout`
refuses a part drawn anywhere larger than its PNG, unless it is stretched to a size like the terrace's one px sky
strip, and a part used once that is still drawn scaled or off a whole unit, unless it sways or turns.
A root file, a screen's file or a stage's `background.json`, is one container the canvas's size at 0,0
holding the scene; `layout` and `stage` refuse any other shape, naming the scene.
A PNG drawn by hand needs no generator: put it in the game's scenes/ and place it in the JSON.

## Backups

Nothing the generator writes is overwritten without a copy. Before a render or `layout` replaces a file,
the old file is moved to `SceneGenerator/build/.backup/<its path>/<name>-<YYYYMMDD-HHMMSS>.<ext>`. The scene
editor keeps its own backups, in `.backup/` under its `--root`.

`build/.manifest.json` maps each PNG's path below the game's scenes/ to the sha256 it had when `layout` copied it
there, and `build/scenes/.manifest.json` does the same for each render. A PNG whose hash no longer matches was
edited since, so it is reported and left alone; a render replaces it only when asked (`--force <path>`), and
backs it up first even then.

## Draw order

A scene draws in file order, parents before their children: later drawables are on top. The sky
comes first, then `clouds` (a group of one ref per cloud), then the landscape, the town and the near
trees, the floor, then the objects back to front.

## Objects and their shadows

Each object in a scene is a drawable with an `id` and `children`. Its shadow is its first child,
so it draws under the object and moving or duplicating the object moves its shadow too. The object
itself is its second child, `<object> object`, a ref to its template (`furniture/planters.json#left-urn`)
placed by a `position` override. A shadow
draws over every object listed before its object, so an object placed close in front of another
can darken the other's base.

## Leaves and flowers

Each leaf, flower and rose is a `ref` to a template in `plants/leaves.json`, `flowers.json` or
`roses.json` with `position`,
`rotation`, `xScale`/`yScale` overrides. The templates set `anchor` and `pivot` to the part's
stem, so a placed leaf rotates and scales around where it grows from. A template exists per
shape and per tone (`lit`, `mid`, `shade`, `dark`), so moving a leaf into the shade is a change of
`ref`, not of colour.

The corner bush, the urn bushes and the crystal planter's two bushes are grown from the library
pieces in `plants/branches.json`, the way a camellia grows:
- each piece is a branch or a rosette template, made of `leaves.json` and `stems.json` instances. A
  branch's side shoots are groups, `<piece> shoot <n>`, placed where each one grows;
- each bush places each piece by one ref, with `position`, `rotation` and `xScale`/`yScale`
  overrides, and a negative `xScale` for a mirrored piece;
- each flower is a sibling of the piece refs, painted after them;
- in the template every ref is named `<object> <template it places> <n>` (`crystal planter daisy-12-36 2`,
  `left urn branch-small-2 1`): which bush a piece grows on isn't in its name.

The terrace's planted objects are drawn as placed in the scene editor: `EsmeTerrace/placements.json`
holds, in canvas units, each object's images and piece refs in draw order with their place, turn, scale and sway
delay, and the edits to the rest of the terrace (clouds and feature cypresses placed, the lake shimmer moved, what
the terrace leaves out, what was added). `EsmeTerrace.generated()` is the terrace as the generators draw it;
`build()` applies the placements to it.

Moving, turning or scaling a piece's ref carries all of its leaves; editing the piece's template
changes every place it grows.
