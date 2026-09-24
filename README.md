# Windows-Laptop-Hibernation-Script-Python

[![CI](https://github.com/farmanullah1/Windows-Laptop-Hibernation-Script-Python/actions/workflows/ci.yml/badge.svg)](https://github.com/farmanullah1/Windows-Laptop-Hibernation-Script-Python/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A reliable, production-ready Python utility to safely hibernate your Windows laptop with a single click from your Desktop, Windows Search, global keyboard shortcut, or automatic low-battery monitor.

---

## Features

- **One-Click Desktop Icon**: A dedicated `Hibernate.lnk` shortcut on your Desktop with a custom modern dark/cyan power & moon icon ([`hibernate.ico`](hibernate.ico)).
- **Windows Search Integration**: Installs into Start Menu Programs so pressing `Win` and typing `Hibernate` immediately finds and runs the script.
- **Global Hotkey (`Ctrl + Alt + H`)**: Hibernate from anywhere without needing to minimize windows or click the desktop.
- **Accidental Click Protection**: Displays a sleek 5-second countdown dialog with a **Cancel** button (`Esc`) or immediate **Hibernate Now** (`Enter`) so you never accidentally interrupt your work.
- **Audio Feedback Chime**: Plays a subtle Windows notification sound when the countdown begins so you have acoustic confirmation when triggering via hotkey.
- **Smart Battery Monitor Daemon (`--monitor`)**: Optional background watcher that automatically and safely hibernates your laptop when the battery hits a critical threshold (e.g. 5%) while unplugged, preventing sudden power loss and unsaved data corruption.
- **Customizable Preferences**: Configure countdown duration, confirmation prompt, force shutdown, audio chime, and hotkey in a clean [`config.json`](config.json).
- **Silent Background Execution**: Runs via `pythonw.exe`, eliminating unsightly flashing black command prompt windows when clicked.
- **Reliable Windows Power Management**: Uses native Windows `shutdown.exe /h` designed for both modern standby (S0 Low Power Idle) and standard S3/S4 sleep architectures, with automated fallback to the `powrprof.dll` Windows API.
- **Production-Grade Rotating Logs**: Automatically rotates logs in [`hibernate.log`](hibernate.log) (max 1MB, 3 backups) to prevent unbounded disk growth.
- **Fail-Safe Error Reporting**: If hibernation is ever disabled in Windows policy, displays an explicit native Windows dialog box with clear recovery instructions.
- **Safe Testing / Dry-Run Mode**: Validate hardware and OS support without actually putting the laptop to sleep.

---

## 1-Click Installation & Setup

If you cloned this repository, simply double-click:
```text
setup.bat
```
This automatically verifies Python, installs dependencies from `requirements.txt`, creates the custom icon, and places the `Hibernate.lnk` shortcut on your **Desktop** and **Start Menu** with the `Ctrl + Alt + H` hotkey configured.

To remove shortcuts at any time, run:
```text
uninstall.bat
```

---

## Configuration (`config.json`)

You can customize the script's behavior by editing [`config.json`](config.json):

```json
{
  "confirm_before_hibernate": true,
  "countdown_seconds": 5,
  "force_kill_apps": false,
  "enable_hotkey": true,
  "hotkey": "Ctrl+Alt+H",
  "play_audio_chime": true,
  "create_start_menu_shortcut": true,
  "battery_monitor": {
    "threshold_percent": 5,
    "check_interval_seconds": 60
  }
}
```

| Setting | Default | Description |
|---|---|---|
| `confirm_before_hibernate` | `true` | Show countdown dialog before hibernating. Set to `false` for instant hibernation. |
| `countdown_seconds` | `5` | Countdown time in seconds before auto-hibernating. |
| `force_kill_apps` | `false` | Pass `/f` flag to force close non-responsive apps. |
| `enable_hotkey` | `true` | Enable global keyboard shortcut on the desktop shortcut. |
| `hotkey` | `"Ctrl+Alt+H"` | Key combination to trigger hibernation from anywhere in Windows. |
| `play_audio_chime` | `true` | Play system notification sound when hibernation is initiated. |
| `create_start_menu_shortcut` | `true` | Create Start Menu shortcut for Windows Search indexing. |
| `battery_monitor.threshold_percent` | `5` | Battery percentage to auto-hibernate when unplugged. |
| `battery_monitor.check_interval_seconds` | `60` | Frequency in seconds to check battery levels. |

---

## Files

- [`hibernate.py`](hibernate.py): The main script that validates power states, displays the countdown dialog, and executes the hibernation command.
- [`create_desktop_shortcut.py`](create_desktop_shortcut.py): Generates the multi-resolution icon, reads [`config.json`](config.json), and creates the Desktop and Start Menu shortcuts.
- [`generate_icon.py`](generate_icon.py): Generates [`hibernate.ico`](hibernate.ico) (resolutions 256×256 down to 16×16).
- [`setup.bat`](setup.bat): 1-click Windows setup batch installer.
- [`uninstall.bat`](uninstall.bat): 1-click clean uninstaller.
- [`requirements.txt`](requirements.txt): Python dependencies (`Pillow`, `psutil`).
- [`config.json`](config.json): Configuration file.
- [`LICENSE`](LICENSE): MIT License.
- [`hibernate.ico`](hibernate.ico): The multi-resolution Windows icon used for the Desktop shortcut.
- [`hibernate.log`](hibernate.log): Auto-rotating execution and diagnostics log.

---

## How to Use

### 1. From Desktop, Windows Search, or Hotkey
- **Double-click** the **Hibernate** icon on your Desktop.
- **Search**: Press the `Windows Key`, type `Hibernate`, and press `Enter`.
- **Keyboard Shortcut**: Press **`Ctrl + Alt + H`** from anywhere.
- A 5-second countdown will appear with a chime. Click **Cancel** (or press `Esc`) if triggered by accident, or let the timer reach zero to hibernate.

### 2. Low-Battery Daemon (Automatic Protection)
To monitor battery in the background and auto-hibernate when below 5%:
```powershell
python hibernate.py --monitor
```

### 3. From Command Line

- **Test prerequisites safely without hibernating**:
  ```powershell
  python hibernate.py --dry-run
  ```

- **Hibernate immediately without countdown**:
  ```powershell
  python hibernate.py --no-confirm
  ```

- **Hibernate and force close hanging apps**:
  ```powershell
  python hibernate.py --force
  ```

- **Recreate or update shortcuts**:
  ```powershell
  python hibernate.py --create-shortcut
  ```

- **Remove shortcuts cleanly**:
  ```powershell
  python create_desktop_shortcut.py --remove
  ```

---

## Testing

Run the automated test suite locally:
```powershell
python -m unittest discover tests
```

---

## System Requirements

- **Operating System**: Windows 10 or Windows 11
- **Python**: Python 3.10+ (configured with `pythonw.exe`)
- **Hibernation Policy**: Hibernation must be enabled in Windows.
  If disabled, open Command Prompt or PowerShell as Administrator and run:
  ```powershell
  powercfg -h on
  ```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
