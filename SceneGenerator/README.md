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
                                .manifest.json, .backup/, previews/, and pixelmator/, the one file
                                Pixelmator opens

panel-attack-references/        reference images (each folder's painting is source.png), by the same folders

<game worktree>/client/assets/themes/Panel Attack Modern/
  scenes/                       what the game draws
    plants/                     leaves, flowers, roses, stems, branches, trees and bushes
      leaves.json               templateOnly drawables, placed with ref
      ...
      parts/<group>/<name>@2x.png
    furniture/                  planters, table-set
    structures/                 houses
    scenery/                    sky, clouds, landscape (the mountains, lake, islands and the meadow)
    EsmeTerrace/
      EsmeTerrace.json          the scene: where everything is placed
      parts/<object>/<name>@2x.png
    MainMenu.json               places the terrace over the main menu's canvas
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
```

`layout` with no names writes every file it makes. A file whose bytes differ from the new output is
moved to the backups first, so writing over an edited file can be undone from there.

Only `@2x` images exist. A `@2x` PNG's pixels are the pixels of the document the art was drawn in
(1536 x 1024 for EsmeTerrace), so the scene's own units are half that: EsmeTerrace is 768 x 512 units.
A PNG drawn by hand needs no generator: put it in the game's scenes/ and place it in the JSON.

## Backups

Nothing the generator writes is overwritten without a copy. Before a render or `layout` replaces a file,
the old file is moved to `SceneGenerator/build/.backup/<its path>/<name>-<YYYYMMDD-HHMMSS>.<ext>`. The scene
editor keeps its own backups, in `.backup/` under its `--root`.

`build/.manifest.json` maps each rendered PNG's path below the game's scenes/ to the sha256 it had when it was
written. A PNG whose hash no longer matches was edited since, so a render reports it and leaves it alone
unless asked to replace it (`--force <path>`), and backs it up first even then.

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
- in the template every ref is named `<object> <template it places> <n>`, numbered in draw order
  (`crystal planter daisy-12-36 2`, `left urn branch-small-2 1`): which bush a piece grows on isn't
  in its name.

Moving, turning or scaling a piece's ref carries all of its leaves; editing the piece's template
changes every place it grows.
