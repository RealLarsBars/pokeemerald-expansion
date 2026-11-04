# Emerald Editor

A small local web app for editing this game without touching code. It runs
with the Python that is already installed for building (no extra packages)
and edits the project's own files, so everything it does is visible in git.

Start it from the **Emerald Editor** desktop shortcut (see `windows/README.md`),
or from a terminal in the project folder:

```console
python3 editor/server.py
```

then open <http://localhost:8765>.

## What it edits

| Tab | What you can change | Files it writes |
| --- | --- | --- |
| Trainers | Battle picture, overworld sprite, name, class, music, single/double, mugshot, starting field effects (terrain, Trick Room...), items, AI, every Pokémon (species, level, item, ability, nature, moves, IVs, EVs, shiny, ball, Tera type, Dynamax level, Gigantamax), what they say before and after battle. Paste or copy Showdown teams. Trainers with the same name are grouped, with all their battles side by side. | `src/data/trainers.party`, `data/maps/*/map.json`, the text files |
| Dialogue | Search every line of text in the game, edit it with a text box preview that flags lines that are too wide, and find and replace across the ticked results. | `data/maps/*/scripts.inc`, `data/scripts/*.inc`, `data/text/*.inc`, `src/strings.c` |
| Game settings | All of pokeemerald-expansion's switches in `include/config/` (about 1,400): battle mechanics by generation, AI, followers, DexNav, level caps, which generations of Pokémon exist, and more. On/off settings are checkboxes, generation settings are dropdowns, and every setting shows its own explanation. | `include/config/*.h` (only the value is changed) |
| Scripts | Edit any map's script file, with helpers that insert common commands: messages, giving items or Pokémon, trainer battles, flags, healing, warps. | `data/maps/*/scripts.inc`, `data/scripts/*.inc` |

Only the trainers and texts you change are rewritten; the rest of each file
stays exactly as it was. Before saving a trainer, the editor checks that every
Pokémon, move, item and ability exists, so a typo cannot break the build.

**Play** runs `make` and opens the ROM in mGBA (the path comes from the
`EMERALD_MGBA` environment variable or `--mgba`). **Update** commits your
edits, then merges the newest version from GitHub, and aborts without changing
anything if the two conflict.

## Code layout

- `server.py`: HTTP server and API routes (localhost only).
- `trainers.py`: reads and writes `trainers.party` and Showdown text.
- `textdb.py`: indexes `.string` texts, converts them to plain text and back.
- `maps.py`: links trainers to the map objects and texts that use them.
- `gamedata.py`: species, moves, items, sprites and other lists read from the C headers.
- `configs.py`: reads and changes the `include/config` switches.
- `tasks.py`: build, play and update jobs.
- `static/`: the page itself (plain HTML, CSS and JavaScript).

Not supported yet: Pokémon data (base stats, types, learnsets, evolutions),
wild encounter tables, trainer party pools, and adding brand new trainers
(they also need an ID in `include/constants/opponents.h`).
