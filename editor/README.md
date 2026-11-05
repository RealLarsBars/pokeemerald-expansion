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
| Pokémon data | Name, category, types, abilities (including hidden), base stats, catch rate, EXP and EV yield, growth rate, friendship, gender ratio, egg groups and cycles, wild held items, height and weight, evolutions (method, level or item, conditions), moves learned by level, and the Pokédex entry. Values that depend on generation settings are shown as your game uses them now. | `src/data/pokemon/species_info/*.h`, `src/data/pokemon/level_up_learnsets/gen_N.h` (the set chosen by `P_LVL_UP_LEARNSETS`) |
| Dialogue | Search every line of text in the game, edit it with a text box preview that flags lines that are too wide, and find and replace across the ticked results. | `data/maps/*/scripts.inc`, `data/scripts/*.inc`, `data/text/*.inc`, `src/strings.c` |
| Game settings | All of pokeemerald-expansion's switches in `include/config/` (about 1,400): battle mechanics by generation, AI, followers, DexNav, level caps, which generations of Pokémon exist, and more. On/off settings are checkboxes, generation settings are dropdowns, and every setting shows its own explanation. | `include/config/*.h` (only the value is changed) |
| Fun Modes | Randomizers (wild Pokémon, trainer teams, starters, with a seed), Hard mode (smart AI, built movesets, held items, hand-built boss teams in `editor/fun/boss_teams.party`, extra double battles, legendaries above a chosen level), level caps tied to badges, free Rare Candy in every shop, and comedy dialogue with one theme at a time: Game of Thrones (the realm's voice, noble houses for every boss, royal decrees, badge-by-badge gossip) or Mad Libs (the player fills in 16 blanks from menus at the start and 4 more after every Gym, and people use those words all game). Game of Thrones is written straight, in the spirit of the books. Every Gym can also become a noble house with its own story (House Gyms switch, `house_gyms.py`): the Keepers of the Crypts, the reavers of Dewford, the Master of Whispers, the dream springs, the faceless, the Mother of Dragons, the Sword Twins and the Lord of the Long Night. Teams, the Gym Guides' advice and the leaders' lines all match, with full six-Pokémon teams under Hard mode, and the TRAINER CARD badges become house sigils (`house_sigils.py`). Story events (`thrones_story.py`) add scenes to the real story: heralds after every badge, the Iron Bank loan and its collector, the Red Wedding in Slateport, the rival as your Hand who betrays you in Lilycove, Wally's oath to the Champion, the Gym Guide's spy confession, and a septa's bell after a white-out. Thrones music (`thrones_music.py`) swaps in original medieval songs for the title screen, Littleroot, Routes 101-103, Gyms and trainer, wild and Gym Leader battles, played with the game's own instruments (`sound/voicegroups/thrones.inc`). Each theme also has its own title screen, its own version of Prof. Birch's opening speech, and hand-written lines for every text in the areas done so far (`editor/fun/rewrites/<theme>/`). Extras for either theme: the hero talks back, adult humor, fake news signs, battle commentary. No joke is used twice. Preview shows every change before Apply. Saved versions, Undo Fun Modes and Reset to base game are on the left. | `src/data/trainers.party`, `src/data/wild_encounters.json`, `src/starter_choose.c`, `include/config/caps.h`, `src/caps.c`, `src/data/items.h`, `data/maps/*/scripts.inc`, `data/scripts/*.inc`, `data/text/*.inc`, `src/battle_message.c`, `src/data/mad_libs.h`, `data/scripts/mad_libs.inc`, `graphics/title_screen/emerald_version.png`, `graphics/title_screen/rayquaza_and_clouds.pal`, `graphics/trainer_card/badges.png`, `sound/songs/midi/*.mid`, `sound/songs/midi/midi.cfg` |
| Scripts | Edit any map's script file, with helpers that insert common commands: messages, giving items or Pokémon, trainer battles, flags, healing, warps. | `data/maps/*/scripts.inc`, `data/scripts/*.inc` |

Only the trainers and texts you change are rewritten; the rest of each file
stays exactly as it was. Before saving a trainer, the editor checks that every
Pokémon, move, item and ability exists, so a typo cannot break the build.

**Save as .gba** asks where to save (the name starts as the date and time, in the folder you used last), builds the game, and writes it there as a new `.gba` file, so each version you make is kept.

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
- `species.py`: reads and edits Pokémon data and level-up moves.
- `configs.py`: reads and changes the `include/config` switches.
- `tasks.py`: build, play and update jobs.
- `funmodes.py`: runs the Fun Modes on an in-memory copy (preview) or for real (apply).
- `fundata.py`: every Pokémon's stats, types, abilities and evolutions, and every move, for the randomizers.
- `sets.py`: builds trainer movesets, items, natures and EVs for Hard mode.
- `comedy.py`, `comedy_themes.py`, `comedy_lines.py`: the comedy themes and their writing.
- `thrones_story.py`: the Game of Thrones story events. New scenes are added to `data/event_scripts.s` and called from small hooks; changed lines in existing scenes are whole-text rewrites. Uses FLAG_UNUSED_0x020 and 0x021 for the loan.
- `thrones_music.py`: the Thrones songs written as text scores (`midi_score.py`); `python3 thrones_music.py` rewrites the .mid files in `fun/music/thrones/`. Any .mid with the same name can replace one. `python3 music_preview.py` (needs numpy) plays them through the game's instrument samples and saves .wav previews.
- `house_sigils.py`: the eight house sigils drawn as text pixel art; `python3 house_sigils.py` (needs Pillow) redraws `fun/title/sigils.png`.
- `title_screen.py`: each theme's title screen. The banners are saved in `fun/title/`; run `python3 title_screen.py` (needs Pillow) only to redraw them.
- `versions.py`: saved versions, Undo Fun Modes and Reset to base game. Versions are git commits under
  `refs/emerald/versions/`, so they never change your history; the editor's own folders are never rolled back.
- `static/`: the page itself (plain HTML, CSS and JavaScript).

Not supported yet: TM/tutor and egg move lists, forms built from shared
templates (Unown, Flabébé colours...), wild encounter tables, trainer party pools, and adding brand new trainers
(they also need an ID in `include/constants/opponents.h`).
