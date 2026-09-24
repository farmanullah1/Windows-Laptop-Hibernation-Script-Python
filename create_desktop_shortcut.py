"""
Automated Desktop & Start Menu Shortcut Creator for Hibernate Script.

Creates Windows shortcuts (.lnk) configured to run `hibernate.py`
using `pythonw.exe` (silent background execution), links them to the custom
high-resolution `hibernate.ico` icon, and assigns the global hotkey (Ctrl+Alt+H).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("CreateShortcut")

PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = PROJECT_DIR / "config.json"


def load_config() -> Dict[str, Any]:
    """Loads configuration options from config.json, returning sensible defaults."""
    default_config: Dict[str, Any] = {
        "confirm_before_hibernate": True,
        "countdown_seconds": 5,
        "force_kill_apps": False,
        "enable_hotkey": True,
        "hotkey": "Ctrl+Alt+H",
        "play_audio_chime": True,
        "create_start_menu_shortcut": True,
    }
    if CONFIG_FILE.is_file():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                default_config.update(loaded)
        except Exception as exc:
            logger.warning("Could not read config.json (%s), using defaults.", exc)
    return default_config


def get_desktop_dir() -> Path:
    """
    Retrieves the actual Windows Desktop directory path, accounting for
    OneDrive folder redirection and customized user profiles.
    """
    try:
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "[Environment]::GetFolderPath('Desktop')",
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=5
        )
        desktop_path = Path(result.stdout.strip())
        if desktop_path.is_dir():
            return desktop_path
    except Exception as exc:
        logger.warning(
            "PowerShell desktop lookup failed: %s. Falling back to default path.",
            exc,
        )

    fallback = Path(os.environ.get("USERPROFILE", "~")).expanduser() / "Desktop"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def get_start_menu_programs_dir() -> Path:
    """
    Retrieves the Start Menu Programs folder path so Windows Search
    can index and launch the script when typing 'Hibernate'.
    """
    try:
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "[Environment]::GetFolderPath('Programs')",
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=5
        )
        programs_path = Path(result.stdout.strip())
        if programs_path.is_dir():
            return programs_path
    except Exception as exc:
        logger.warning("PowerShell Programs folder lookup failed: %s", exc)

    app_data = Path(os.environ.get("APPDATA", "~")).expanduser()
    fallback = app_data / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def find_pythonw_executable() -> Path:
    """
    Locates pythonw.exe corresponding to the current Python environment.
    Using pythonw.exe prevents a black command prompt window from flashing.
    """
    current_exe = Path(sys.executable)
    exe_dir = current_exe.parent

    candidates = [
        exe_dir / "pythonw.exe",
        exe_dir / "Scripts" / "pythonw.exe",
        Path(sys.prefix) / "pythonw.exe",
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    logger.warning("pythonw.exe not found; falling back to %s", current_exe)
    return current_exe


def ensure_icon_exists(icon_path: Path) -> Path:
    """Ensures hibernate.ico exists; generates it if missing."""
    if not icon_path.is_file():
        logger.info("hibernate.ico not found. Generating now...")
        from generate_icon import create_ico_file

        create_ico_file(icon_path)
    return icon_path


def create_single_shortcut(
    shortcut_path: Path,
    target_exe: Path,
    arguments: str,
    working_dir: Path,
    icon_path: Path,
    description: str,
    hotkey: str = "",
) -> Path:
    """Creates a Windows shortcut using WScript.Shell COM object via PowerShell."""
    ps_script = f"""
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut(@'
{shortcut_path}
'@)
$shortcut.TargetPath = @'
{target_exe}
'@
$shortcut.Arguments = '{arguments}'
$shortcut.WorkingDirectory = @'
{working_dir}
'@
$shortcut.IconLocation = @'
{icon_path}
'@ + ',0'
$shortcut.Description = '{description}'
if ('{hotkey}') {{
    $shortcut.Hotkey = '{hotkey}'
}}
$shortcut.Save()
"""
    cmd = ["powershell", "-NoProfile", "-Command", ps_script]
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0:
        raise RuntimeError(f"Failed to create shortcut at {shortcut_path}: {res.stderr.strip()}")

    if not shortcut_path.is_file():
        raise RuntimeError(f"Shortcut was not created at expected location: {shortcut_path}")

    return shortcut_path


def create_all_shortcuts(force_recreate: bool = True) -> List[Path]:
    """
    Creates shortcuts on both the Desktop and the Start Menu Programs folder.
    """
    config = load_config()
    script_path = PROJECT_DIR / "hibernate.py"
    icon_path = ensure_icon_exists(PROJECT_DIR / "hibernate.ico")
    pythonw_path = find_pythonw_executable()
    hotkey_str = config.get("hotkey", "Ctrl+Alt+H") if config.get("enable_hotkey", True) else ""
    created: List[Path] = []

    # 1. Desktop Shortcut
    desktop_dir = get_desktop_dir()
    desktop_shortcut = desktop_dir / "Hibernate.lnk"
    create_single_shortcut(
        shortcut_path=desktop_shortcut,
        target_exe=pythonw_path,
        arguments=f'"{script_path}"',
        working_dir=PROJECT_DIR,
        icon_path=icon_path,
        description="Hibernate Laptop - Save state and power down",
        hotkey=hotkey_str,
    )
    logger.info("Created Desktop shortcut at: %s", desktop_shortcut)
    created.append(desktop_shortcut)

    # 2. Start Menu Programs Shortcut (Allows Windows Search indexing)
    if config.get("create_start_menu_shortcut", True):
        start_menu_dir = get_start_menu_programs_dir()
        start_menu_shortcut = start_menu_dir / "Hibernate.lnk"
        create_single_shortcut(
            shortcut_path=start_menu_shortcut,
            target_exe=pythonw_path,
            arguments=f'"{script_path}"',
            working_dir=PROJECT_DIR,
            icon_path=icon_path,
            description="Hibernate Laptop - Save state and power down",
            hotkey="",  # Only assign hotkey to desktop shortcut to prevent conflict
        )
        logger.info("Created Start Menu shortcut at: %s", start_menu_shortcut)
        created.append(start_menu_shortcut)

    return created


def create_shortcut() -> Path:
    """Backwards-compatible helper returning the primary Desktop shortcut path."""
    shortcuts = create_all_shortcuts()
    return shortcuts[0]


if __name__ == "__main__":
    try:
        paths = create_all_shortcuts()
        print("\n[SUCCESS] Shortcuts created:")
        for p in paths:
            print(f"  - {p}")
    except Exception as e:
        print(f"\n[ERROR] Failed to create shortcuts: {e}", file=sys.stderr)
        sys.exit(1)
