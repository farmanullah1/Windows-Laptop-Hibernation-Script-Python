"""
Automated Desktop Shortcut Creator for Hibernate Script.

Creates a Windows desktop shortcut (.lnk) configured to run `hibernate.py`
using `pythonw.exe` (silent execution without a flashing console window),
links it to the custom high-resolution `hibernate.ico` icon, and assigns
an optional global hotkey (e.g. Ctrl+Alt+H).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("CreateShortcut")

PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = PROJECT_DIR / "config.json"


def load_config() -> dict:
    """Loads configuration options from config.json, returning sensible defaults."""
    default_config = {
        "confirm_before_hibernate": True,
        "countdown_seconds": 5,
        "force_kill_apps": False,
        "enable_hotkey": True,
        "hotkey": "Ctrl+Alt+H",
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


def find_pythonw_executable() -> Path:
    """
    Locates pythonw.exe corresponding to the current Python environment.
    Using pythonw.exe prevents a black command prompt window from flashing
    when the shortcut is clicked.
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


def create_shortcut(
    shortcut_name: str = "Hibernate.lnk",
    force_recreate: bool = True,
) -> Path:
    """
    Creates or updates the desktop shortcut pointing to hibernate.py.

    Args:
        shortcut_name: Name of the shortcut file on the Desktop.
        force_recreate: Overwrite existing shortcut if True.

    Returns:
        Path to the created desktop shortcut.
    """
    config = load_config()
    script_path = PROJECT_DIR / "hibernate.py"
    icon_path = ensure_icon_exists(PROJECT_DIR / "hibernate.ico")
    pythonw_path = find_pythonw_executable()
    desktop_dir = get_desktop_dir()
    shortcut_path = desktop_dir / shortcut_name

    hotkey_str = config.get("hotkey", "Ctrl+Alt+H") if config.get("enable_hotkey", True) else ""

    if shortcut_path.exists() and not force_recreate:
        logger.info("Shortcut already exists at %s", shortcut_path)
        return shortcut_path

    # Build PowerShell script to create shortcut via WScript.Shell COM object
    ps_script = f"""
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut(@'
{shortcut_path}
'@)
$shortcut.TargetPath = @'
{pythonw_path}
'@
$shortcut.Arguments = '"' + @'
{script_path}
'@ + '"'
$shortcut.WorkingDirectory = @'
{PROJECT_DIR}
'@
$shortcut.IconLocation = @'
{icon_path}
'@ + ',0'
$shortcut.Description = 'Hibernate Laptop - Save state and power down'
if ('{hotkey_str}') {{
    $shortcut.Hotkey = '{hotkey_str}'
}}
$shortcut.Save()
"""

    cmd = ["powershell", "-NoProfile", "-Command", ps_script]
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0:
        err_msg = f"Failed to create shortcut: {res.stderr.strip()}"
        logger.error(err_msg)
        raise RuntimeError(err_msg)

    if not shortcut_path.is_file():
        raise RuntimeError(f"Shortcut was not created at expected location: {shortcut_path}")

    logger.info("Successfully created desktop shortcut:")
    logger.info("  Location: %s", shortcut_path)
    logger.info("  Target: %s", pythonw_path)
    logger.info("  Arguments: \"%s\"", script_path)
    logger.info("  Icon: %s", icon_path)
    if hotkey_str:
        logger.info("  Global Hotkey: %s", hotkey_str)

    return shortcut_path


if __name__ == "__main__":
    try:
        created_path = create_shortcut()
        print(f"\n[SUCCESS] Desktop shortcut created at: {created_path}")
    except Exception as e:
        print(f"\n[ERROR] Failed to create shortcut: {e}", file=sys.stderr)
        sys.exit(1)
