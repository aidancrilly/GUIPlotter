# GUIPlotter

Python-based desktop app for quickly plotting common analysis data without depending on Origin. The initial release focuses on whitespace-delimited column files that contain a single header row.

## Install

```bash
uv pip install --system -e .
```

This installs three commands:

| Command | Purpose |
| --- | --- |
| `guiplotter` | Launch the GUI |
| `guiplotter-space` | Alias of `guiplotter` (space-delimited loader) |
| `guiplotter-make-app` | Build a double-clickable macOS app bundle |

### If the commands are "not found"

The install put them in your interpreter's `bin` directory, which is not always
on `PATH`. Find it and add it to your shell profile:

```bash
python3 -c 'import sysconfig; print(sysconfig.get_path("scripts"))'
# e.g. /Library/Frameworks/Python.framework/Versions/3.14/bin
echo 'export PATH="<that path>:$PATH"' >> ~/.zshrc && exec zsh
```

Alternatively, `uv tool install .` installs the commands into `~/.local/bin`,
which uv already keeps on `PATH`.

## Launching from the Dock (macOS)

```bash
guiplotter-make-app          # creates ~/Applications/GUIPlotter.app
```

Open it once from Finder, then right-click its Dock icon and choose
**Options → Keep in Dock**. It also shows up in Spotlight and Launchpad.

Useful flags:

- `--destination /Applications` to install for every user on the machine
- `--force` to overwrite an existing bundle

The bundle is a thin launcher around the *installed* package, not a frozen copy
of it, so edits to the source take effect the next time you open the app — no
rebuild needed. Rebuild only if you move or recreate the Python environment it
was built from. Because it is not a self-contained app, it will not run on a
machine that lacks this environment; use [py2app](https://py2app.readthedocs.io)
or [PyInstaller](https://pyinstaller.org) if you need something distributable.

### Other platforms

There is no bundle builder for Linux or Windows yet. On Linux, write a
`~/.local/share/applications/guiplotter.desktop` file pointing `Exec=` at the
`guiplotter` command. On Windows, create a shortcut to the `guiplotter.exe`
generated in your environment's `Scripts` directory and pin it to the taskbar —
it is registered as a GUI script, so it opens without a console window.

## Usage

You can run the app on any platform that supports Tkinter. After launching, click **Open Files** to choose one or more space-delimited files (columns separated by whitespace, header row required). Use the controls to assign series to axes, tweak labels, and press **Plot** to render the lines.
