"""
Automated Desktop Shortcut Creator for Hibernate Script.

Creates a Windows desktop shortcut (.lnk) configured to run `hibernate.py`
using `pythonw.exe` (silent execution without a flashing console window)
and links it to the custom high-resolution `hibernate.ico` icon.
"""

from __future__ import annotations

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


def get_desktop_dir() -> Path:
    """
    Retrieves the actual Windows Desktop directory path, accounting for
    OneDrive folder redirection and customized user profiles.
    """
    try:
        # PowerShell query for the exact Shell Desktop folder path
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

    # Fallback to standard user desktop
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
    project_dir = Path(__file__).resolve().parent
    script_path = project_dir / "hibernate.py"
    icon_path = ensure_icon_exists(project_dir / "hibernate.ico")
    pythonw_path = find_pythonw_executable()
    desktop_dir = get_desktop_dir()
    shortcut_path = desktop_dir / shortcut_name

    if shortcut_path.exists() and not force_recreate:
        logger.info("Shortcut already exists at %s", shortcut_path)
        return shortcut_path

    # Build PowerShell script to create shortcut via WScript.Shell COM object
    # Using parameterized script to avoid injection or quote escaping errors
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
{project_dir}
'@
$shortcut.IconLocation = @'
{icon_path}
'@ + ',0'
$shortcut.Description = 'Hibernate Laptop - Save state and power down'
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

    return shortcut_path


if __name__ == "__main__":
    try:
        created_path = create_shortcut()
        print(f"\n[SUCCESS] Desktop shortcut created at: {created_path}")
    except Exception as e:
        print(f"\n[ERROR] Failed to create shortcut: {e}", file=sys.stderr)
        sys.exit(1)
