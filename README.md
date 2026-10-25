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
  ```

## Setup & Usage
1. Place the script in a dedicated folder and run it.
2. On first launch, follow the prompts to select the required executables:
   - **Hypergryph's `Arknights.exe`** (the TC client to intercept).
   - **Yostar's `Arknights.exe`** (the EN client to launch).
   - **Yostar's Launcher executable** (`Arknights_EN_Gamelauncher.exe`, used when a client update is required).
3. Your paths are saved in a `paths.txt` file next to the script.
4. Once configured, an Arknights icon will appear in your **system tray** indicating that the swapper is active. Right-click the icon to pause it, force a game update via the Yostar launcher, or quit altogether.

## Run on Startup (Optional)

**Method 1: Startup Folder (Standard)**
1. Press `Win + R`, type `shell:startup`, and press **Enter** (or type `shell:startup` directly into the Windows Explorer address bar).
2. Create a **shortcut** to the `.py` script and place that shortcut inside the Startup folder.
*(Note: Because the script requires Administrator privileges to intercept processes, Windows may display a UAC prompt at login with this method.)*

**Method 2: Task Scheduler (Silent / No UAC Prompt)**
1. Open **Task Scheduler** and click **Create Task**.
2. In the **General** tab, name the task and check **Run with highest privileges**.
3. In the **Triggers** tab, add a new trigger set to **At log on**.
4. In the **Actions** tab, set the program/script to your `pythonw.exe` path and add the full path to `"Swap Arknights.py"` (in quotes) in the **Add arguments** field.
