# Windows setup

These files set up this project on Windows so that the whole game lives in one
folder you can edit, and a desktop shortcut builds your changes and opens them
in mGBA.

## First time

1. Install [mGBA](https://mgba.io/downloads.html) if you have not already.
2. Double-click `Setup.bat` and leave the window open until it says **All done!**
   - Windows asks for permission to install WSL (the Linux layer used to build
     the game). Click **Yes**.
   - If it asks you to restart, restart. Setup carries on by itself after you
     log back in.
   - The first build takes roughly 5 to 15 minutes.
3. If it cannot find mGBA, a window opens so you can pick `mGBA.exe`.

You now have two desktop shortcuts:

- **Emerald Project** opens the game folder. Everything the game is made from
  is in there.
- **Play Emerald** rebuilds only what you changed (usually well under a minute)
  and opens the game in mGBA.

## Good to know

- The game folder lives inside Ubuntu (WSL), which makes builds much faster than
  a normal Windows folder. Its address looks like
  `\\wsl.localhost\Ubuntu\root\Emerald`. It shows up as **Linux** in the left
  side of File Explorer.
- Nothing changes in the game until you press **Play Emerald**. The game cannot
  pick up changes while it is running, so close mGBA, make your edits, then
  press Play again.
- Your save file (`pokeemerald.sav`) sits next to the game in the project
  folder and survives rebuilds.
- Settings are stored in `%LOCALAPPDATA%\EmeraldTools\config.json`. Running
  `Setup.bat` again is safe: it skips anything that is already done.
