"""
Windows Laptop Hibernation Script.

Puts the machine into hibernation (S4 sleep state) safely and reliably.
When invoked directly or via desktop shortcut (with pythonw.exe),
executes silently. Errors are logged to hibernate.log and presented
via native Windows dialog boxes.
"""

from __future__ import annotations

import argparse
import ctypes
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple

# Setup local directory and file logging
PROJECT_DIR = Path(__file__).resolve().parent
LOG_FILE = PROJECT_DIR / "hibernate.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("HibernateScript")


def show_native_message(title: str, message: str, is_error: bool = True) -> None:
    """
    Displays a native Windows message box.
    Useful when executed via pythonw.exe where no console is attached.
    """
    if sys.platform == "win32":
        # MB_ICONERROR = 0x10, MB_ICONINFORMATION = 0x40, MB_OK = 0x0
        icon_flag = 0x10 if is_error else 0x40
        try:
            ctypes.windll.user32.MessageBoxW(0, message, title, icon_flag | 0x0)
        except Exception as exc:
            logger.error("Failed to show message box: %s", exc)


def check_system_support() -> Tuple[bool, str]:
    """
    Verifies whether the current operating system is Windows and if
    Hibernation is currently supported and enabled.

    Returns:
        Tuple of (is_supported: bool, diagnostic_message: str)
    """
    if sys.platform != "win32":
        return False, "This script is designed for Windows operating systems only."

    try:
        result = subprocess.run(
            ["powercfg", "/a"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        output = result.stdout or ""

        # Check for Hibernate under available sleep states
        available_section = output.split("The following sleep states are not available")[0]
        if "Hibernate" in available_section:
            return True, "Hibernate is supported and enabled on this system."

        return (
            False,
            "Hibernate is not enabled in Windows power policy.\n"
            "To enable it, open Command Prompt or PowerShell as Administrator and run:\n\n"
            "powercfg -h on\n\n"
            "Then run this script again.",
        )
    except Exception as exc:
        return False, f"Could not determine power state availability: {exc}"


def hibernate_system(force: bool = False, dry_run: bool = False) -> bool:
    """
    Executes the hibernation sequence.

    Args:
        force: If True, forces applications to close/save without warning.
        dry_run: If True, tests prerequisites without actually hibernating.

    Returns:
        True if hibernation command was dispatched successfully, False otherwise.
    """
    logger.info("Initiating hibernation check (force=%s, dry_run=%s)", force, dry_run)

    is_supported, message = check_system_support()
    if not is_supported:
        logger.error("Pre-check failed: %s", message)
        show_native_message("Hibernation Not Available", message, is_error=True)
        return False

    if dry_run:
        logger.info("[DRY RUN] System verified: %s", message)
        logger.info("[DRY RUN] Hibernation command would be: shutdown /h%s", " /f" if force else "")
        return True

    # Primary method: Windows native shutdown.exe /h
    # This works properly on both standard S3/S4 systems and Modern Standby (S0) systems.
    cmd = ["shutdown.exe", "/h"]
    if force:
        cmd.append("/f")

    logger.info("Executing system command: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            logger.info("Hibernation command dispatched successfully.")
            return True

        stderr = (result.stderr or "").strip()
        logger.warning(
            "shutdown.exe /h returned code %d: %s. Attempting fallback API...",
            result.returncode,
            stderr,
        )
    except Exception as exc:
        logger.warning("Failed to invoke shutdown.exe: %s. Attempting fallback API...", exc)

    # Fallback method: ctypes call to powrprof.dll SetSuspendState
    try:
        logger.info("Invoking powrprof.dll SetSuspendState(bHibernate=True)...")
        # SetSuspendState(bHibernate, bForce, bWakeupEventsDisabled)
        success = bool(ctypes.windll.powrprof.SetSuspendState(1, 1 if force else 0, 0))
        if success:
            logger.info("SetSuspendState returned True.")
            return True
        logger.error("SetSuspendState returned False.")
    except Exception as exc:
        logger.error("SetSuspendState raised exception: %s", exc)

    err_text = (
        "Failed to initiate hibernation.\n\n"
        "Please verify that hibernation is enabled by opening Command Prompt "
        "as Administrator and running:\n"
        "powercfg -h on\n\n"
        f"See {LOG_FILE} for details."
    )
    show_native_message("Hibernate Failed", err_text, is_error=True)
    return False


def main() -> None:
    """Command-line interface entry point."""
    parser = argparse.ArgumentParser(
        description="Safely hibernate Windows laptop/PC and manage desktop shortcut.",
    )
    parser.add_argument(
        "--dry-run",
        "--check",
        action="store_true",
        dest="dry_run",
        help="Validate environment and system hibernation readiness without putting PC to sleep.",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force running applications to close and proceed with hibernation.",
    )
    parser.add_argument(
        "--create-shortcut",
        action="store_true",
        help="Generate or recreate the desktop shortcut and custom icon.",
    )

    args = parser.parse_args()

    if args.create_shortcut:
        from create_desktop_shortcut import create_shortcut

        shortcut_path = create_shortcut()
        print(f"[OK] Desktop shortcut verified at: {shortcut_path}")
        return

    success = hibernate_system(force=args.force, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
