# Windows setup

These files set up this project on Windows so that the whole game lives in one
folder, the **Emerald Editor** can change it, and one click builds your changes
and opens them in mGBA.

## Download

Get **EmeraldSetup.zip** from the newest release:
<https://github.com/RealLarsBars/pokeemerald-expansion/releases/latest/download/EmeraldSetup.zip>
(it is rebuilt automatically whenever these setup files change). Unzip it
anywhere, for example your Desktop.

## First time

1. Install [mGBA](https://mgba.io/downloads.html) if you have not already.
2. Double-click `Setup.bat` and leave the window open until it says **All done!**
   - Windows asks for permission to install WSL (the Linux layer used to build
     the game). Click **Yes**.
   - If it asks you to restart, restart. Setup carries on by itself after you
     log back in.
   - It asks where the game folder should go. **Yes** puts it inside Ubuntu
     (recommended: builds are fastest there). **No** lets you pick a folder on
     your PC, for example on another drive; setup makes an `Emerald` folder
     inside it. Avoid folders synced by OneDrive. This is only asked on the
     first install; later runs keep the folder you chose.
   - The first build takes roughly 5 to 15 minutes.
3. If it cannot find mGBA, a window opens so you can pick `mGBA.exe`.

You now have three desktop shortcuts:

- **Emerald Editor** opens the editor (trainers, Pokémon data, dialogue,
  scripts, game settings) in its own window, with its own Play and Update
  buttons. It points at `EmeraldEditor.exe` in `%LOCALAPPDATA%\EmeraldTools`,
  which you can also pin to the taskbar or Start menu. The editor keeps running
  quietly in the background after you close its window, so it opens instantly
  next time; restarting the PC stops it. If it has a problem starting, a message
  box shows what went wrong.
- **Emerald Project** opens the game folder. Everything the game is made from
  is in there.
- **Play Emerald** rebuilds only what you changed (usually a few seconds) and
  opens the game in mGBA, without opening the editor.

## Good to know

- By default the game folder lives inside Ubuntu (WSL), which makes builds much
  faster than a normal Windows folder. Its address looks like
  `\\wsl.localhost\Ubuntu\root\Emerald`. It shows up as **Linux** in the left
  side of File Explorer. The **Emerald Project** shortcut always opens the
  folder, wherever you put it.
- Nothing changes in the game until you press **Play**. The game cannot pick up
  changes while it is running, so close mGBA, make your edits, then press Play
  again.
- Your save file (`pokeemerald.sav`) sits next to the game in the project
  folder and survives rebuilds.
- **Update** in the editor saves your own changes first, then brings in new
  editor features from GitHub. If an update touches the same lines you edited,
  it stops and changes nothing.
- Settings are stored in `%LOCALAPPDATA%\EmeraldTools\config.json`. Running
  `Setup.bat` again is safe: it skips anything that is already done.
