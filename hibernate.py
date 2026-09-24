"""
Windows Laptop Hibernation Script & Battery Monitor Daemon.

Puts the machine into hibernation (S4 sleep state) safely and reliably.
When invoked directly or via desktop shortcut (with pythonw.exe),
executes silently. Errors are logged to rotating log files and presented
via native Windows dialog boxes.

Features:
- Accidental trigger protection with a 5-second Tkinter countdown dialog.
- Global Hotkey (Ctrl+Alt+H) and Start Menu Search integration.
- Optional audible feedback chime via winsound.
- Battery Monitor Daemon (--monitor): auto-hibernates when battery drops to critical level.
- Configurable settings via config.json.
- Primary method: shutdown.exe /h; fallback: powrprof.dll SetSuspendState.
- Production-grade rotating file logging.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import subprocess
import sys
import time
import tkinter as tk
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import winsound
except ImportError:
    winsound = None

try:
    import psutil
except ImportError:
    psutil = None

PROJECT_DIR = Path(__file__).resolve().parent
LOG_FILE = PROJECT_DIR / "hibernate.log"
CONFIG_FILE = PROJECT_DIR / "config.json"

# Production-grade log rotation: max 1MB per file, up to 3 backups
log_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=1_000_000,
    backupCount=3,
    encoding="utf-8",
)
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
log_handler.setFormatter(log_formatter)

logger = logging.getLogger("HibernateScript")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.addHandler(logging.StreamHandler(sys.stdout))


def load_config() -> Dict[str, Any]:
    """Loads configuration options from config.json with fallback defaults."""
    default_config: Dict[str, Any] = {
        "confirm_before_hibernate": True,
        "countdown_seconds": 5,
        "force_kill_apps": False,
        "enable_hotkey": True,
        "hotkey": "Ctrl+Alt+H",
        "play_audio_chime": True,
        "create_start_menu_shortcut": True,
        "battery_monitor": {
            "threshold_percent": 5,
            "check_interval_seconds": 60,
        },
    }
    if CONFIG_FILE.is_file():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                default_config.update(loaded)
        except Exception as exc:
            logger.warning("Could not parse config.json (%s); using default settings.", exc)
    return default_config


def play_chime() -> None:
    """Plays a subtle Windows notification chime asynchronously."""
    if winsound is not None:
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception as exc:
            logger.debug("Failed to play audio chime: %s", exc)


def show_native_message(title: str, message: str, is_error: bool = True) -> None:
    """Displays a native Windows message box."""
    if sys.platform == "win32":
        icon_flag = 0x10 if is_error else 0x40  # MB_ICONERROR or MB_ICONINFORMATION
        try:
            ctypes.windll.user32.MessageBoxW(0, message, title, icon_flag | 0x0)
        except Exception as exc:
            logger.error("Failed to show message box: %s", exc)


def prompt_countdown(seconds: int = 5, reason: str = "") -> bool:
    """
    Displays a modern, sleek countdown dialog centered on the screen.
    Allows user to cancel hibernation or trigger it immediately.

    Returns:
        True if confirmed (or timer elapsed); False if cancelled.
    """
    if seconds <= 0:
        return True

    state = {"confirmed": False, "cancelled": False, "remaining": seconds}

    try:
        root = tk.Tk()
        root.title("Hibernate Laptop")
        root.configure(bg="#0f172a")  # Slate 900
        root.attributes("-topmost", True)
        root.resizable(False, False)

        # Center on primary display
        w, h = 400, 210
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        root.geometry(f"{w}x{h}+{x}+{y}")

        icon_path = PROJECT_DIR / "hibernate.ico"
        if icon_path.is_file():
            try:
                root.iconbitmap(str(icon_path))
            except Exception:
                pass

        frame = tk.Frame(root, bg="#0f172a", padx=22, pady=18)
        frame.pack(fill="both", expand=True)

        header_text = "Critical Battery Hibernation" if reason else "Preparing Hibernation"
        title_lbl = tk.Label(
            frame,
            text=header_text,
            font=("Segoe UI", 12, "bold"),
            fg="#f8fafc",
            bg="#0f172a",
        )
        title_lbl.pack(anchor="w")

        countdown_text = f"Hibernating in {seconds} seconds..."
        if reason:
            countdown_text = f"{reason} - Hibernating in {seconds}s..."

        countdown_lbl = tk.Label(
            frame,
            text=countdown_text,
            font=("Segoe UI", 10),
            fg="#38bdf8",  # Sky-400
            bg="#0f172a",
        )
        countdown_lbl.pack(anchor="w", pady=(6, 12))

        note_lbl = tk.Label(
            frame,
            text="Press Esc to cancel or Enter to hibernate now.",
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg="#0f172a",
        )
        note_lbl.pack(anchor="w", pady=(0, 16))

        btn_frame = tk.Frame(frame, bg="#0f172a")
        btn_frame.pack(fill="x", side="bottom")

        def on_confirm(*_) -> None:
            state["confirmed"] = True
            root.destroy()

        def on_cancel(*_) -> None:
            state["cancelled"] = True
            root.destroy()

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=("Segoe UI", 9, "bold"),
            bg="#334155",
            fg="#e2e8f0",
            activebackground="#475569",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=4,
            cursor="hand2",
            command=on_cancel,
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        hibernate_btn = tk.Button(
            btn_frame,
            text="Hibernate Now",
            font=("Segoe UI", 9, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=4,
            cursor="hand2",
            command=on_confirm,
        )
        hibernate_btn.pack(side="right")

        root.bind("<Escape>", on_cancel)
        root.bind("<Return>", on_confirm)
        root.protocol("WM_DELETE_WINDOW", on_cancel)

        def tick() -> None:
            if state["cancelled"] or state["confirmed"]:
                return
            state["remaining"] -= 1
            if state["remaining"] <= 0:
                state["confirmed"] = True
                root.destroy()
            else:
                secs_str = f"{state['remaining']} second{'s' if state['remaining'] > 1 else ''}"
                if reason:
                    countdown_lbl.config(text=f"{reason} - In {secs_str}...")
                else:
                    countdown_lbl.config(text=f"Hibernating in {secs_str}...")
                root.after(1000, tick)

        root.after(1000, tick)
        root.mainloop()

        if state["cancelled"]:
            logger.info("Hibernation cancelled by user.")
            return False

        return state["confirmed"]
    except Exception as exc:
        logger.warning("Countdown dialog could not be displayed (%s); proceeding.", exc)
        return True


def check_system_support() -> Tuple[bool, str]:
    """
    Verifies whether the operating system is Windows and if
    Hibernation is currently supported and enabled.
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


def hibernate_system(
    force: bool = False,
    dry_run: bool = False,
    skip_confirm: bool = False,
    reason: str = "",
) -> bool:
    """
    Executes the hibernation sequence.

    Args:
        force: If True, forces applications to close/save without warning.
        dry_run: If True, tests prerequisites without actually hibernating.
        skip_confirm: If True, skips countdown confirmation dialog.
        reason: Optional context message (e.g., 'Battery critical: 4%').

    Returns:
        True if hibernation command was dispatched successfully, False otherwise.
    """
    config = load_config()
    should_confirm = config.get("confirm_before_hibernate", True) and not skip_confirm
    countdown_secs = int(config.get("countdown_seconds", 5))
    force = force or bool(config.get("force_kill_apps", False))
    play_audio = bool(config.get("play_audio_chime", True))

    logger.info(
        "Initiating hibernation sequence (force=%s, dry_run=%s, confirm=%s, reason='%s')",
        force,
        dry_run,
        should_confirm,
        reason,
    )

    is_supported, message = check_system_support()
    if not is_supported:
        logger.error("Pre-check failed: %s", message)
        show_native_message("Hibernation Not Available", message, is_error=True)
        return False

    if play_audio and not dry_run:
        play_chime()

    if should_confirm and not dry_run:
        proceed = prompt_countdown(seconds=countdown_secs, reason=reason)
        if not proceed:
            return False

    if dry_run:
        logger.info("[DRY RUN] System verified: %s", message)
        logger.info("[DRY RUN] Hibernation command would be: shutdown /h%s", " /f" if force else "")
        return True

    # Primary method: Windows native shutdown.exe /h
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


def run_battery_monitor(
    threshold_percent: Optional[int] = None,
    interval_seconds: Optional[int] = None,
    dry_run: bool = False,
) -> None:
    """
    Background daemon that monitors battery level and auto-hibernates
    when the laptop battery drops to or below the critical threshold.
    """
    if psutil is None:
        logger.error("psutil package is required for battery monitoring. Run: pip install psutil")
        sys.exit(1)

    config = load_config()
    b_conf = config.get("battery_monitor", {})
    threshold = threshold_percent or int(b_conf.get("threshold_percent", 5))
    interval = interval_seconds or int(b_conf.get("check_interval_seconds", 60))

    logger.info("Starting Battery Monitor Daemon...")
    logger.info("  Threshold: %d%%", threshold)
    logger.info("  Check Interval: %d seconds", interval)
    logger.info("  Dry-Run Mode: %s", dry_run)

    print(f"[DAEMON] Monitoring battery (Threshold: {threshold}%, Check every {interval}s). Press Ctrl+C to stop.")

    try:
        while True:
            battery = psutil.sensors_battery()
            if battery is None:
                logger.warning("No battery hardware detected (Desktop or unsupported). Exiting monitor.")
                print("[WARNING] No battery sensor found on this machine.")
                return

            percent = battery.percent
            plugged = battery.power_plugged

            logger.debug("Battery check: %d%% (AC Plugged: %s)", percent, plugged)

            if not plugged and percent <= threshold:
                reason_msg = f"Battery critical ({percent}% remaining)"
                logger.warning("CRITICAL BATTERY REACHED: %d%% <= %d%% while discharging!", percent, threshold)
                hibernate_system(force=True, dry_run=dry_run, reason=reason_msg)
                if not dry_run:
                    return

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[DAEMON] Battery monitor stopped by user.")
        logger.info("Battery monitor daemon stopped by user.")


def main() -> None:
    """Command-line interface entry point."""
    parser = argparse.ArgumentParser(
        description="Safely hibernate Windows laptop/PC and manage desktop/start menu shortcuts.",
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
        "--no-confirm",
        "--now",
        action="store_true",
        dest="no_confirm",
        help="Skip the countdown/confirmation prompt and hibernate immediately.",
    )
    parser.add_argument(
        "--create-shortcut",
        action="store_true",
        help="Generate or recreate Desktop and Start Menu shortcuts with hotkeys and icon.",
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Run background battery daemon to auto-hibernate when battery is critically low.",
    )
    parser.add_argument(
        "--battery-threshold",
        type=int,
        default=None,
        help="Battery percentage threshold to trigger auto-hibernation (default from config.json: 5).",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Battery check interval in seconds (default from config.json: 60).",
    )

    args = parser.parse_args()

    if args.create_shortcut:
        from create_desktop_shortcut import create_all_shortcuts

        paths = create_all_shortcuts()
        print("[OK] Shortcuts successfully updated:")
        for p in paths:
            print(f"  - {p}")
        return

    if args.monitor:
        run_battery_monitor(
            threshold_percent=args.battery_threshold,
            interval_seconds=args.interval,
            dry_run=args.dry_run,
        )
        return

    success = hibernate_system(
        force=args.force,
        dry_run=args.dry_run,
        skip_confirm=args.no_confirm,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
