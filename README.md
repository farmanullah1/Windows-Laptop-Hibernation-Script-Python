# Windows-Laptop-Hibernation-Script-Python

A reliable, production-ready Python utility to safely hibernate your Windows laptop with a single click from your Desktop.

---

## Features

- **One-Click Desktop Icon**: A dedicated `Hibernate.lnk` shortcut on your Windows Desktop with a custom modern dark/cyan power & moon icon (`hibernate.ico`).
- **Silent Background Execution**: Runs via `pythonw.exe`, eliminating unsightly flashing black command prompt windows when clicked.
- **Reliable Windows Power Management**: Uses native Windows `shutdown.exe /h` designed for both modern standby (S0 Low Power Idle) and standard S3/S4 sleep architectures, with an automated fallback to the `powrprof.dll` Windows API.
- **Fail-Safe Error Reporting**: If hibernation is ever disabled in Windows policy, displays an explicit native Windows dialog box with clear recovery instructions and logs details to `hibernate.log`.
- **Safe Testing / Dry-Run Mode**: Allows verifying hardware/OS support without putting the laptop to sleep.

---

## Files

- [`hibernate.py`](hibernate.py): The main script that validates power states and executes the system hibernation command.
- [`create_desktop_shortcut.py`](create_desktop_shortcut.py): Automatically generates the multi-resolution icon and creates the desktop shortcut.
- [`generate_icon.py`](generate_icon.py): Generates `hibernate.ico` (resolutions 256x256 down to 16x16).
- [`hibernate.ico`](hibernate.ico): The multi-resolution Windows icon used for the Desktop shortcut.
- [`hibernate.log`](hibernate.log): Execution and diagnostics log.

---

## How to Use

### 1. From Desktop (Double-Click)
Simply double-click the **Hibernate** icon on your Desktop. Your laptop will save its current session to disk and power down into hibernation. When you turn it back on, all your open apps and work will be restored.

### 2. From Command Line

- **Test prerequisites safely without hibernating**:
  ```powershell
  python hibernate.py --dry-run
  ```

- **Hibernate immediately**:
  ```powershell
  python hibernate.py
  ```

- **Hibernate and force close hanging apps**:
  ```powershell
  python hibernate.py --force
  ```

- **Recreate or update Desktop shortcut**:
  ```powershell
  python hibernate.py --create-shortcut
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
