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
   - The first build takes roughly 5 to 15 minutes.
3. If it cannot find mGBA, a window opens so you can pick `mGBA.exe`.

You now have three desktop shortcuts:

- **Emerald Editor** opens the editor (trainers, dialogue, scripts) with its own
  Play and Update buttons. A minimized `wsl` window appears on the taskbar while
  the editor runs; closing that window closes the editor.
- **Emerald Project** opens the game folder. Everything the game is made from
  is in there.
- **Play Emerald** rebuilds only what you changed (usually a few seconds) and
  opens the game in mGBA, without opening the editor.

## Good to know

- The game folder lives inside Ubuntu (WSL), which makes builds much faster than
  a normal Windows folder. Its address looks like
  `\\wsl.localhost\Ubuntu\root\Emerald`. It shows up as **Linux** in the left
  side of File Explorer.
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
