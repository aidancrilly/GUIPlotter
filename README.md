# GUIPlotter

Python-based desktop app for quickly plotting common analysis data without depending on Origin. The initial release focuses on whitespace-delimited column files that contain a single header row.

## Getting Started

```bash
pip install -e .
guiplotter-space  # or: python -m guiplotter
```

You can run the app on any platform that supports Tkinter. After launching, click **Open Files** to choose one or more space-delimited files (columns separated by whitespace, header row required). Use the controls to assign series to axes, tweak labels, and press **Plot** to render the lines.
