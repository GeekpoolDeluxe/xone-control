# Changelog

## 0.1.1

- Fixed GTK combo/menu foreground and background colors on Linux Mint so select menus stay readable.
- Added individual controller power-off support for newer `xone` drivers exposing `/sys/bus/usb/drivers/xone-dongle/*/active_clients` and `poweroff`.
- Added controller power-off actions to the desktop panel tray menu.
- Updated LED mode handling for the `dlundqvist/xone` fork, including modes `0`, `1`, `2`, `3`, `4`, `8`, and `9`.
- Changed LED writes to apply mode before brightness and verify the resulting sysfs values after saving.
- Added the controller icon to the GTK window and desktop launcher so it appears in the taskbar/window list.
