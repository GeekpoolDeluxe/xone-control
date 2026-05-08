# xone Control

Small GTK interface for checking and controlling local `xone` controller state.

## Features

- Shows connected `xone` controller status.
- Shows battery information from `/sys/class/power_supply/gip*`.
- Shows and changes LED brightness and LED mode from `/sys/class/leds/gip*`.
- Lists loaded `xone_*` kernel modules.
- Lists installed `xone_dongle_*.bin` firmware files.
- Shows recent xone-related kernel messages.
- Can load the xone modules through `pkexec`.
- Includes German and English interface texts.
- Adds a desktop panel indicator that shows connection state and battery level.
- Uses a single-instance lock so starting it twice will not open a second copy.

## Start

Run:

```bash
/home/denis/xone-control/start-xone-control.sh
```

Start directly in the panel without opening the main window:

```bash
/home/denis/xone-control/start-xone-control.sh --hidden
```

## Requirements

This application is only a local interface for an already installed `xone` driver. It does not install or replace the kernel driver.

Required system setup:

- `xone` kernel driver installed and working.
- Dongle firmware installed if the Xbox Wireless Dongle is used.
- A connected `xone` device that exposes `/sys/class/power_supply/gip*` and/or `/sys/class/leds/gip*`.

The original `xone` project is:

```text
https://github.com/medusalix/xone
```

That repository is in maintenance mode. An actively maintained fork can also be used. The UI only depends on the installed driver exposing the usual `xone` sysfs paths.

The app itself is a Python 3 GTK application. It does not need to be compiled, but these runtime packages must be installed:

- `python3`
- `python3-gi`
- `gir1.2-gtk-3.0`
- `policykit-1` or a compatible package that provides `pkexec`
- `gir1.2-ayatanaappindicator3-0.1` for the panel indicator

On Linux Mint/Ubuntu:

```bash
sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 policykit-1
```

`pkexec` is only needed for actions that require elevated rights, such as loading kernel modules or writing LED settings when sysfs is not writable by the current user.

If Ayatana AppIndicator is not available, the app falls back to GTK's older status icon support. Depending on the desktop environment, that fallback may not show a visible battery label in the panel.

## Secure Boot Note

If Secure Boot is enabled, avoid loading local build artifacts with `sudo make load`. Use the DKMS-installed modules through `modprobe`, which is what the app's module button does.

## Autostart on Ubuntu and Linux Mint

Use the hidden start mode for autostart so only the panel indicator appears and the main window stays closed.

### Graphical Setup

On Linux Mint:

1. Open `Startup Applications`.
2. Click `Add`.
3. Use `xone Control` as the name.
4. Use this command:

```bash
/home/denis/xone-control/start-xone-control.sh --hidden
```

On Ubuntu:

1. Open `Startup Applications Preferences`.
2. Click `Add`.
3. Use `xone Control` as the name.
4. Use this command:

```bash
/home/denis/xone-control/start-xone-control.sh --hidden
```

### Manual Setup

Create this file:

```text
~/.config/autostart/xone-control.desktop
```

With this content:

```ini
[Desktop Entry]
Type=Application
Name=xone Control
Comment=Panel indicator for xone controller status and battery
Exec=/home/denis/xone-control/start-xone-control.sh --hidden
Icon=input-gaming
Terminal=false
X-GNOME-Autostart-enabled=true
```

The app uses a single-instance lock, so accidentally starting it twice will not create a second running copy.

## Languages

The interface uses the `TRANSLATIONS` dictionary in `xone_control.py`.

The selected language is saved in:

```text
~/.config/xone-control/config.json
```

The single-instance lock is stored in:

```text
~/.cache/xone-control/xone-control.lock
```

To add another language:

1. Copy the existing `"en"` block in `TRANSLATIONS`.
2. Change the language code, for example `"fr"`.
3. Translate every value.
4. Set `"language_name"` to the name shown in the language selector.

If a key is missing in a new language, the app falls back to the English default for that key.

## Files

- `xone_control.py`: GTK application.
- `start-xone-control.sh`: launcher script.
- `xone-control.desktop`: optional desktop launcher.
