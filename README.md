# Arknights-Global-X-Hypergryph-Launcher

A lightweight background utility that silently intercepts the Hypergryph (GRYPHLINK) Arknights client and swaps it with the Yostar (Global/EN) Arknights client, while forcing the GRYPHLINK launcher to minimize to the taskbar.

## Features
- **Silent Interception:** Automatically kills the TC client upon launch and starts the EN client in its place.
- **Forced Minimize:** Prevents the GRYPHLINK launcher from restoring its window when the intercepted TC process closes.
- **Update Fallback:** Automatically triggers the Yostar launcher if the EN client closes shortly after launch due to a mandatory client update.
- **System Tray Control:** Toggle the swapper, manually launch the Yostar updater, or exit directly from the system tray.

## Requirements
- Windows OS
- Python 3.x
- Required Python packages:
  ```bash
  pip install psutil pystray Pillow pywin32
