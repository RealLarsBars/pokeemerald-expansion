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
| Trainers | Battle picture, overworld sprite, name, class, music, single/double, mugshot, starting field effects (terrain, Trick Room...), items, AI, every Pokémon (species, level, item, ability, nature, moves, IVs, EVs, shiny, ball, Tera type, Dynamax level, Gigantamax), what they say before and after battle. Paste or copy Showdown teams. **Make competitive** gives the whole team strong sets in one click (best ability, four good moves, a held item, nature, EVs, perfect IVs, smarter AI; click again for different sets). Trainers with the same name are grouped, with all their battles side by side. | `src/data/trainers.party`, `data/maps/*/map.json`, the text files |
| Maps | A picture of every map, drawn from its tilesets. Place item balls and hidden items by clicking the map, drag items and people to move them, change items and amounts. Per map: wild Pokémon (grass, surfing, Rock Smash, each fishing rod; species, levels, how often), what the shop sells and item prices, gift Pokémon and one-time encounters (Castform, Beldum, fossils, legendaries), and the trainers there. **+ New trainer** adds a brand new trainer standing on the map, with a battle script and their lines. | `data/maps/*/map.json`, `src/data/wild_encounters.json`, `data/maps/*/scripts.inc`, `src/data/items.h` (prices), `include/constants/opponents.h` and `src/data/trainers.party` (new trainers) |
| Pokémon data | Name, category, types, abilities (including hidden), base stats, catch rate, EXP and EV yield, growth rate, friendship, gender ratio, egg groups and cycles, wild held items, height and weight, evolutions (method, level or item, conditions), moves learned by level, TMs, HMs and tutor moves it can learn, egg moves, and the Pokédex entry. Values that depend on generation settings are shown as your game uses them now. Also: the three **starter Pokémon** and their level, and the **TM & HM list** (which move each one teaches). | `src/data/pokemon/species_info/*.h`, `src/data/pokemon/level_up_learnsets/gen_N.h` (the set chosen by `P_LVL_UP_LEARNSETS`), `src/data/pokemon/all_learnables.json`, `src/data/pokemon/egg_moves.h`, `include/constants/tms_hms.h`, `src/starter_choose.c` |
| Dialogue | Search every line of text in the game, edit it with a text box preview that flags lines that are too wide, and find and replace across the ticked results. | `data/maps/*/scripts.inc`, `data/scripts/*.inc`, `data/text/*.inc`, `src/strings.c` |
| Game settings | All of pokeemerald-expansion's switches in `include/config/` (about 1,400): battle mechanics by generation, AI, followers, DexNav, level caps, which generations of Pokémon exist, and more. On/off settings are checkboxes, generation settings are dropdowns, and every setting shows its own explanation. | `include/config/*.h` (only the value is changed) |
| Fun Modes | Every Universal Pokémon Randomizer (ZX) setting that exists in Emerald, in collapsible groups with presets (`editor/randomizer.py`): base stats, types, abilities, evolutions (random or every level), evolution helpers (trade, high-level and time evolutions), one EXP curve, Pokémon colors; starters, gifts and legendaries, roamers, Wally's catching lesson, in-game trades; move data (power, accuracy, PP, type, category), level-up movesets (or Metronome only); TM moves, TM compatibility, tutor moves, tutor compatibility; trainer teams (fair, anything, type themed, new Gym types) plus names, class names, levels, extra Pokémon, held items, fully evolved, all doubles; wild Pokémon (per area, 1 to 1, type themed, catch 'em all) plus levels, catch rates and held items; items on the ground, hidden items, shops, Pickup; the type chart (shuffle, keep identities, random, inverse); quality of life switches. Plus our own modes: Hard mode (smart AI, built movesets, held items, hand-built boss teams in `editor/fun/boss_teams.party`, extra double battles, legendaries above a chosen level), level caps tied to badges, free Rare Candy in every shop, and comedy dialogue with one theme at a time: Game of Thrones (the realm's voice, noble houses for every boss, royal decrees, badge-by-badge gossip) or Mad Libs (the player fills in 16 blanks from menus at the start and 4 more after every Gym, and people use those words all game). Game of Thrones is written straight, in the spirit of the books. Every Gym can also become a noble house with its own story (House Gyms switch, `house_gyms.py`): the Keepers of the Crypts, the reavers of Dewford, the Master of Whispers, the dream springs, the faceless, the Mother of Dragons, the Sword Twins and the Lord of the Long Night. Teams, the Gym Guides' advice and the leaders' lines all match, with full six-Pokémon teams under Hard mode, and the TRAINER CARD badges become house sigils (`house_sigils.py`). Story events (`thrones_story.py`) add scenes to the real story: heralds after every badge, the Iron Bank loan and its collector, the Red Wedding in Slateport, the rival as your Hand who betrays you in Lilycove, Wally's oath to the Champion, the Gym Guide's spy confession, and a septa's bell after a white-out. Thrones music (`thrones_music.py`) swaps in original medieval songs for the title screen, Littleroot, Routes 101-103, Gyms and trainer, wild and Gym Leader battles, played with the game's own instruments (`sound/voicegroups/thrones.inc`). Each theme also has its own title screen, its own version of Prof. Birch's opening speech, and hand-written lines for every text in the areas done so far (`editor/fun/rewrites/<theme>/`). Extras for either theme: the hero talks back, adult humor, fake news signs, battle commentary. No joke is used twice. Preview shows every change before Apply. Saved versions, Undo Fun Modes and Reset to base game are on the left. | `src/data/pokemon/species_info/*.h`, `src/data/pokemon/level_up_learnsets/gen_N.h`, `src/data/pokemon/all_learnables.json`, `include/constants/tms_hms.h`, `src/data/moves_info.h`, `src/data/types_info.h`, `src/data/trade.h`, `data/scripts/move_tutors.inc`, `graphics/pokemon/*/*.pal`, `include/config/*.h`, `src/new_game.c`, `src/data/trainers.party`, `src/data/wild_encounters.json`, `src/starter_choose.c`, `include/fun_level_caps.h`, `src/caps.c`, `src/data/items.h`, `data/maps/*/scripts.inc`, `data/scripts/*.inc`, `data/text/*.inc`, `src/battle_message.c`, `src/data/mad_libs.h`, `data/scripts/mad_libs.inc`, `graphics/title_screen/emerald_version.png`, `graphics/title_screen/rayquaza_and_clouds.pal`, `graphics/trainer_card/badges.png`, `sound/songs/midi/*.mid`, `sound/songs/midi/midi.cfg` |
| Scripts | Edit any map's script file. **Simple view** shows each script as steps in plain words (messages with a text box preview, items, Pokémon, battles, flags, warps...), with boxes to change them and buttons to add, move or delete steps. **Code view** is the file itself, with helpers that insert common commands. | `data/maps/*/scripts.inc`, `data/scripts/*.inc` |

Only the trainers and texts you change are rewritten; the rest of each file
stays exactly as it was. Before saving a trainer, the editor checks that every
Pokémon, move, item and ability exists, so a typo cannot break the build.

**Save as .gba** asks where to save (the name starts as the date and time, in the folder you used last), builds the game, and writes it there as a new `.gba` file, so each version you make is kept.

**Stop** (in the build panel) ends a build or save that is taking too long or is stuck, so the editor is free again.

**Play** runs `make` and opens the ROM in mGBA (the path comes from the
`EMERALD_MGBA` environment variable or `--mgba`). **Update** commits your
edits, then merges the newest version of the editor from GitHub. If both changed
the same lines, it asks which version to keep (see below). The editor also does
this by itself each time it opens (turn it off in the Update window). That
automatic update skips quietly when offline, when a job is running, or when an
update touches lines you edited, and the Update button shows a badge instead.

**Team** lets friends work on one game. Each person keeps their own game folder
and builds it themselves; the team's game lives in a private GitHub repository
(remote `team`, branch `main`) that the owner's editor makes with **Start a team
game**. Everyone signs in once with a GitHub personal access token (kept in
`~/.config/emerald-editor/github.json`, never in the game folder). The owner
invites friends by GitHub username; friends click **Join**, which accepts the
invite and merges the team's game into their folder. **Share my changes**
commits (with an optional note), merges what friends shared, and pushes.
**Get friends' changes** only merges. **Keep everyone up to date automatically** (on by default, per folder, `git config emerald.autoSync`) makes the page do both about once a minute while nothing is unsaved, no job is running and no window is open, then reloads what is on screen. When the same lines changed on both sides,
the merge stays open and the editor shows each clash side by side with Keep
mine, Keep theirs or Keep both (whole-file choice for pictures and deleted
files); Cancel aborts the merge. New editor features still come from the public
repository through Update and reach friends through the team copy too.

**Team codes**: the owner makes a fine-grained GitHub token limited to the team repository (Contents: read and write) and the editor wraps it with the repository name into a code starting `EMERALD-`. Friends paste the code and their name in Team to join, with no GitHub account; their changes carry that name. Anyone with the code can change the game; the owner locks people out by deleting that token on GitHub and making a new code.

**Projects** (📁 at the top left) keeps several games side by side, such as your own hack and team games. Each project is a full game folder with its own edits, builds, saved versions and team. New projects go in `Emerald-Projects/<name>` next to the first game folder and are made with a local `git clone`, so nothing big is downloaded: *Original game* resets to `origin/master` (the newest editor, none of your edits), and *Copy of this game* keeps everything. Opening a project restarts the editor from that folder's own `editor/server.py`, and the next start opens the project used last (`~/.config/emerald-editor/projects.json`). A GitHub sign-in is shared by all projects; a team code is kept with its project only (`.git/emerald-team.json`).

## Code layout

- `server.py`: HTTP server and API routes (localhost only).
- `trainers.py`: reads and writes `trainers.party` and Showdown text.
- `textdb.py`: indexes `.string` texts, converts them to plain text and back.
- `maps.py`: links trainers to the map objects and texts that use them.
- `gamedata.py`: species, moves, items, sprites and other lists read from the C headers.
- `species.py`: reads and edits Pokémon data and level-up moves.
- `configs.py`: reads and changes the `include/config` switches.
- `tasks.py`: build, play and update jobs (and stopping them).
- `projects.py`: the list of game folders, making new ones and switching between them (`static/projects.js`).
- `team.py`: team games (GitHub sign-in, invites, share and get changes, picking versions when changes clash). Page side in `static/team.js`.
- `mapview.py`: draws maps from their tilesets (a small PNG reader/writer, no extra packages) and saves items and positions; new items get a `FLAG_UNUSED_*` flag nothing else uses.
- `wild.py`: wild Pokémon per map. `shops.py`: Poké Mart lists and prices. `gifts.py`: starters, gifts and one-time encounters.
- `newtrainer.py`: adds a trainer ID (the game has room for 9 more), a team, and the person and script on a map.
- `movesets.py`: TM/HM list (renames the TM items everywhere when a TM's move changes), TM/tutor moves per Pokémon and egg moves.
- `static/world.js` (Maps tab), `static/learn.js` (starters, TMs), `static/steps.js` (scripts simple view).
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

Not supported yet: forms built from shared templates (Unown, Flabébé
colours...), trainer party pools, changing the number of TMs, and drawing
or reshaping maps (use Porymap for that).
