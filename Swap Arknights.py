import os
import subprocess
import ctypes
import sys
import time
import threading
import configparser
import traceback
import psutil
import pystray
from PIL import Image, ImageDraw
import win32gui
import win32ui
import win32con
import win32api
import win32process

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "paths.txt")

TC_EXE = ""
EN_EXE = ""
EN_DIR = ""
LAUNCHER_DIR = ""
YOSTAR_LAUNCHER_EXE = ""
YOSTAR_LAUNCHER_DIR = ""

# threshold in seconds under which game exit is treated as an update abort
UPDATE_EXIT_THRESHOLD = 45

swap_active = True
running = True
mutex_handle = None

def setup_silent_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        pythonw = sys.executable.replace("python.exe", "pythonw.exe").replace("py.exe", "pyw.exe")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", pythonw, f'"{os.path.abspath(__file__)}"', None, 0
        )
        sys.exit()
    
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)

def ensure_single_instance():
    global mutex_handle
    # keep reference in global scope to prevent garbage collection from releasing mutex
    mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, "ArknightsSwapper_SingleInstance_Mutex")
    # 183 is ERROR_ALREADY_EXISTS
    if ctypes.windll.kernel32.GetLastError() == 183:
        ctypes.windll.user32.MessageBoxW(
            0,
            "Arknights Swapper is already running.",
            "Arknights Swapper - Error",
            win32con.MB_ICONERROR | win32con.MB_OK
        )
        sys.exit(1)

def ask_exe_path(title):
    try:
        # use native Win32 file dialog to avoid tkinter dependency issues
        filename, _, _ = win32gui.GetOpenFileNameW(
            InitialDir=SCRIPT_DIR,
            Flags=win32con.OFN_FILEMUSTEXIST | win32con.OFN_PATHMUSTEXIST | win32con.OFN_EXPLORER,
            File="",
            DefExt="exe",
            Title=title,
            Filter="Executable (*.exe)\0*.exe\0All Files (*.*)\0*.*\0"
        )
        return filename
    except Exception:
        # user cancelled dialog
        return ""

def load_or_prompt_paths():
    global TC_EXE, EN_EXE, EN_DIR, LAUNCHER_DIR, YOSTAR_LAUNCHER_EXE, YOSTAR_LAUNCHER_DIR
    config = configparser.ConfigParser()
    
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE, encoding="utf-8")
    
    tc_path = config.get("Paths", "tc_exe", fallback="")
    en_path = config.get("Paths", "en_exe", fallback="")
    yostar_path = config.get("Paths", "yostar_launcher_exe", fallback="")
    
    if not (os.path.isfile(tc_path) and os.path.isfile(en_path) and os.path.isfile(yostar_path)):
        prompts = [
            ("tc_exe", "Select the Arknights TC executable to intercept (The Hypergryph one) (e.g., GRYPHLINK\\games\\Arknights_TC\\Arknights.exe)", tc_path),
            ("en_exe", "Select the Arknights EN executable to launch (The Yostar one) (e.g., YostarGames\\Arknights_EN\\Arknights.exe)", en_path),
            ("yostar_launcher_exe", "Select the Yostar Launcher executable (To be able to update when big update aren't managed directly in game) (e.g., Arknights_EN_Gamelauncher.exe)", yostar_path)
        ]
        
        if "Paths" not in config:
            config["Paths"] = {}
            
        for key, desc, current_val in prompts:
            if not os.path.isfile(current_val):
                ctypes.windll.user32.MessageBoxW(
                    0, desc, "Initial Setup - Arknights Swapper", win32con.MB_ICONINFORMATION | win32con.MB_OK
                )
                selected = ask_exe_path(desc)
                if not selected:
                    ctypes.windll.user32.MessageBoxW(
                        0, "Setup cancelled. The application will now exit.", "Arknights Swapper - Error", win32con.MB_ICONERROR | win32con.MB_OK
                    )
                    sys.exit(1)
                config["Paths"][key] = os.path.normpath(selected)
            else:
                config["Paths"][key] = os.path.normpath(current_val)
                
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            config.write(f)
        
        tc_path = config["Paths"]["tc_exe"]
        en_path = config["Paths"]["en_exe"]
        yostar_path = config["Paths"]["yostar_launcher_exe"]

    TC_EXE = os.path.normcase(tc_path)
    EN_EXE = en_path
    EN_DIR = os.path.dirname(EN_EXE)
    
    # derive GRYPHLINK root directory by stepping two levels up from .../GRYPHLINK/games/Arknights_TC/Arknights.exe
    LAUNCHER_DIR = os.path.normcase(os.path.dirname(os.path.dirname(os.path.dirname(tc_path))))
    
    YOSTAR_LAUNCHER_EXE = yostar_path
    YOSTAR_LAUNCHER_DIR = os.path.dirname(YOSTAR_LAUNCHER_EXE)

def get_exe_icon(exe_path):
    try:
        # extract embedded icon directly from game binary via Win32 GDI
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)
        large, small = win32gui.ExtractIconEx(exe_path, 0)
        if small:
            win32gui.DestroyIcon(small[0])
        if large:
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
            hdc = hdc.CreateCompatibleDC()
            hdc.SelectObject(hbmp)
            hdc.DrawIcon((0, 0), large[0])
            win32gui.DestroyIcon(large[0])
            bmpinfo = hbmp.GetInfo()
            bmpstr = hbmp.GetBitmapBits(True)
            return Image.frombuffer('RGBA', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRA', 0, 1)
    except Exception:
        pass
    
    # fallback icon if extraction fails
    img = Image.new('RGBA', (64, 64), (30, 30, 30, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([16, 16, 48, 48], fill=(255, 180, 0, 255))
    return img

def minimize_launcher():
    target_pids = set()
    for p in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            exe = os.path.normcase(p.info['exe'] or "")
            name = (p.info['name'] or "").lower()
            # match any process inside launcher directory or named gryphlink
            if (exe and exe.startswith(LAUNCHER_DIR)) or "gryphlink" in name:
                target_pids.add(p.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    def enum_cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid in target_pids:
                # SW_FORCEMINIMIZE bypasses custom Qt/frameless window handlers
                win32gui.ShowWindow(hwnd, win32con.SW_FORCEMINIMIZE)
        return True

    if target_pids:
        win32gui.EnumWindows(enum_cb, None)

def launch_yostar_updater(icon=None, item=None):
    target = os.path.normcase(EN_EXE)
    for p in psutil.process_iter(['exe']):
        try:
            if p.info['exe'] and os.path.normcase(p.info['exe']) == target:
                p.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    if os.path.exists(YOSTAR_LAUNCHER_EXE):
        subprocess.Popen([YOSTAR_LAUNCHER_EXE], cwd=YOSTAR_LAUNCHER_DIR)

def monitor_en_session(proc_en):
    # if game exits shortly after launch, assume version mismatch and trigger Yostar launcher
    try:
        proc_en.wait(timeout=UPDATE_EXIT_THRESHOLD)
        if running and swap_active:
            launch_yostar_updater()
    except subprocess.TimeoutExpired:
        pass

def is_en_running():
    target = os.path.normcase(EN_EXE)
    for p in psutil.process_iter(['exe']):
        try:
            if p.info['exe'] and os.path.normcase(p.info['exe']) == target:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def intercept_loop():
    while running:
        if swap_active:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() == "arknights.exe":
                        exe_path = proc.info['exe'] or proc.exe()
                        if os.path.normcase(exe_path) == TC_EXE:
                            proc.kill()
                            proc.wait(timeout=3)
                            
                            if not is_en_running():
                                proc_en = subprocess.Popen([EN_EXE], cwd=EN_DIR)
                                threading.Thread(target=monitor_en_session, args=(proc_en,), daemon=True).start()
                            
                            # poll during cooldown to catch delayed launcher auto-restore on game exit
                            end_time = time.time() + 3.0
                            while time.time() < end_time and running:
                                minimize_launcher()
                                time.sleep(0.1)
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
        time.sleep(0.2)

def toggle_swap(icon, item):
    global swap_active
    swap_active = not swap_active
    icon.title = "Arknights: Swapper Active" if swap_active else "Arknights: Swapper Paused"

def quit_app(icon, item):
    global running
    running = False
    icon.stop()

if __name__ == "__main__":
    try:
        setup_silent_admin()
        ensure_single_instance()
        load_or_prompt_paths()
        
        # run process watcher in daemon thread so pystray can own main thread
        monitor_thread = threading.Thread(target=intercept_loop, daemon=True)
        monitor_thread.start()
        
        icon_img = get_exe_icon(EN_EXE)
        menu = pystray.Menu(
            pystray.MenuItem("Swapper Active", toggle_swap, checked=lambda item: swap_active, default=True),
            pystray.MenuItem("Launch Yostar Launcher (Force Update)", launch_yostar_updater),
            pystray.MenuItem("Quit", quit_app)
        )
        
        tray = pystray.Icon("ArknightsSwapper", icon_img, "Arknights: Swapper Active", menu)
        tray.run()
    except Exception:
        ctypes.windll.user32.MessageBoxW(
            0, traceback.format_exc(), "Arknights Swapper - Crash", win32con.MB_ICONERROR | win32con.MB_OK
        )
