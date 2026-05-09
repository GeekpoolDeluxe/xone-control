#!/usr/bin/env python3
import glob
import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
except (ImportError, ValueError):
    AppIndicator = None


APP_TITLE = "xone Control"
APP_VERSION = "0.1.1"
POLL_SECONDS = 3
DEFAULT_LANGUAGE = "en"
CONFIG_DIR = Path.home() / ".config" / "xone-control"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = Path.home() / ".cache" / "xone-control"
LOCK_FILE = CACHE_DIR / "xone-control.lock"
APP_DIR = Path(__file__).resolve().parent
ICON_DIR = APP_DIR / "icon"
TRAY_CONNECTED_ICON = "xbox-series-x-green"
TRAY_CONNECTED_ICON_PATH = ICON_DIR / f"{TRAY_CONNECTED_ICON}.svg"
TRAY_DISCONNECTED_ICON = "xbox-series-x-filled"
TRAY_DISCONNECTED_ICON_PATH = ICON_DIR / f"{TRAY_DISCONNECTED_ICON}.svg"
APP_ICON_PATH = ICON_DIR / "xbox-series-x-green.svg"

TRANSLATIONS = {
    "de": {
        "language_name": "Deutsch",
        "subtitle": "Status, Akku und LED-Steuerung für xone-Geräte",
        "language": "Sprache",
        "controller": "Controller",
        "controller_power": "Controller ausschalten",
        "tray_controller_power": "Controller ausschalten",
        "tray_power_off_controller": "{target} ausschalten",
        "shutdown_controller": "Ausschalten",
        "unavailable": "Nicht verfügbar",
        "led": "LED",
        "driver": "Treiber",
        "kernel_messages": "Kernelmeldungen",
        "mode_off": "Aus",
        "mode_on": "An",
        "mode_blink_fast": "Schnell blinken",
        "mode_blink_normal": "Blinken",
        "mode_blink_slow": "Langsam blinken",
        "mode_fade_slow": "Langsam pulsieren",
        "mode_fade_fast": "Schnell pulsieren",
        "set_led": "LED setzen",
        "refresh": "Aktualisieren",
        "load_modules": "Module laden",
        "no_controller": "Kein xone Controller erkannt",
        "connect_controller": "Controller verbinden oder neu pairen.",
        "no_shutdown_target": "Controller-Ausschalten wird von diesem xone-Treiber nicht bereitgestellt.",
        "controller_slot": "{dongle} · Client {slot}",
        "device_fallback": "xone Gerät",
        "unknown": "Unbekannt",
        "connected": "Verbunden  {model}",
        "no_led": "Keine xone LED gefunden",
        "brightness": "{device} · Helligkeit {brightness}/{max_brightness}",
        "no_modules": "keine xone-Module geladen",
        "no_firmware": "keine Dongle-Firmware gefunden",
        "modules": "Module",
        "firmware": "Firmware",
        "no_kernel_messages": "Keine xone-Meldungen in den letzten Kernelzeilen.",
        "saved": "Gespeichert",
        "led_not_applied": "LED-Änderung wurde nicht übernommen.",
        "no_permission_pkexec_missing": "Keine Rechte, und pkexec ist nicht installiert",
        "change_not_applied": "Änderung wurde nicht übernommen",
        "no_led_short": "Keine LED gefunden.",
        "modules_loaded": "Module geladen.",
        "pkexec_missing": "pkexec ist nicht installiert.",
        "modules_load_failed": "Module konnten nicht geladen werden.",
        "controller_shutdown_sent": "Ausschalten an {target} gesendet.",
        "controller_shutdown_failed": "Controller konnte nicht ausgeschaltet werden.",
        "tray_status": "Status",
        "tray_battery": "Akku",
        "tray_show": "Fenster anzeigen",
        "tray_hide": "Fenster ausblenden",
        "tray_quit": "Beenden",
        "tray_connected": "Verbunden",
        "tray_disconnected": "Nicht verbunden",
        "tray_tooltip": "{status} · Akku: {battery}",
    },
    "en": {
        "language_name": "English",
        "subtitle": "Status, battery and LED controls for xone devices",
        "language": "Language",
        "controller": "Controller",
        "controller_power": "Controller power",
        "tray_controller_power": "Controller power",
        "tray_power_off_controller": "Power off {target}",
        "shutdown_controller": "Power off",
        "unavailable": "Unavailable",
        "led": "LED",
        "driver": "Driver",
        "kernel_messages": "Kernel messages",
        "mode_off": "Off",
        "mode_on": "On",
        "mode_blink_fast": "Fast blink",
        "mode_blink_normal": "Blink",
        "mode_blink_slow": "Slow blink",
        "mode_fade_slow": "Slow pulse",
        "mode_fade_fast": "Fast pulse",
        "set_led": "Set LED",
        "refresh": "Refresh",
        "load_modules": "Load modules",
        "no_controller": "No xone controller detected",
        "connect_controller": "Connect or pair the controller again.",
        "no_shutdown_target": "Controller power-off is not exposed by this xone driver.",
        "controller_slot": "{dongle} · client {slot}",
        "device_fallback": "xone device",
        "unknown": "Unknown",
        "connected": "Connected  {model}",
        "no_led": "No xone LED found",
        "brightness": "{device} · Brightness {brightness}/{max_brightness}",
        "no_modules": "no xone modules loaded",
        "no_firmware": "no dongle firmware found",
        "modules": "Modules",
        "firmware": "Firmware",
        "no_kernel_messages": "No xone messages in the latest kernel lines.",
        "saved": "Saved",
        "led_not_applied": "LED change was not applied.",
        "no_permission_pkexec_missing": "No permission, and pkexec is not installed",
        "change_not_applied": "Change was not applied",
        "no_led_short": "No LED found.",
        "modules_loaded": "Modules loaded.",
        "pkexec_missing": "pkexec is not installed.",
        "modules_load_failed": "Modules could not be loaded.",
        "controller_shutdown_sent": "Power-off sent to {target}.",
        "controller_shutdown_failed": "Controller could not be powered off.",
        "tray_status": "Status",
        "tray_battery": "Battery",
        "tray_show": "Show window",
        "tray_hide": "Hide window",
        "tray_quit": "Quit",
        "tray_connected": "Connected",
        "tray_disconnected": "Disconnected",
        "tray_tooltip": "{status} · Battery: {battery}",
    },
}


def tr(language, key, **values):
    text = TRANSLATIONS.get(language, TRANSLATIONS[DEFAULT_LANGUAGE]).get(
        key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    )
    return text.format(**values) if values else text


def load_config():
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(config):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        return True
    except OSError:
        return False


def acquire_single_instance_lock():
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        lock_handle = LOCK_FILE.open("w", encoding="utf-8")
        fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_handle.write(str(os.getpid()))
        lock_handle.flush()
        return lock_handle
    except OSError:
        return None


def read_text(path, default=""):
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return default


def run_text(command):
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        return str(exc).strip()


def write_sysfs(path, value, language):
    try:
        Path(path).write_text(str(value), encoding="utf-8")
        return True, tr(language, "saved")
    except OSError:
        command = [
            "pkexec",
            "sh",
            "-c",
            "printf '%s' \"$1\" > \"$2\"",
            "sh",
            str(value),
            str(path),
        ]
        try:
            subprocess.check_call(command)
            return True, tr(language, "saved")
        except FileNotFoundError:
            return False, tr(language, "no_permission_pkexec_missing")
        except subprocess.CalledProcessError:
            return False, tr(language, "change_not_applied")


def list_xone_modules():
    output = run_text(["lsmod"])
    modules = []
    for line in output.splitlines():
        if line.startswith("xone_"):
            modules.append(line.split()[0])
    return modules


def firmware_files():
    return sorted(Path("/lib/firmware").glob("xone_dongle_*.bin"))


def power_supplies():
    supplies = []
    for path in sorted(glob.glob("/sys/class/power_supply/gip*")):
        supplies.append(Path(path))
    return supplies


def led_devices():
    leds = []
    for path in sorted(glob.glob("/sys/class/leds/gip*")):
        leds.append(Path(path))
    return leds


def xone_dongles():
    dongles = []
    for path in sorted(glob.glob("/sys/bus/usb/drivers/xone-dongle/*")):
        path = Path(path)
        if (path / "poweroff").exists():
            dongles.append(path)
    return dongles


def active_client_slots(dongle):
    active_clients = read_text(dongle / "active_clients")
    slots = []
    for token in active_clients.replace("\t", " ").split():
        if token.startswith("[") and "]*" in token:
            slot = token[1 : token.index("]")]
            if slot.isdigit():
                slots.append(int(slot))
    if slots:
        return slots

    count_text = active_clients.splitlines()[0] if active_clients else ""
    if count_text.isdigit():
        count = int(count_text)
        if count == 1:
            return [0]
        if count > 1:
            return list(range(16))
    return slots


class XoneControl(Gtk.Window):
    def __init__(self):
        super().__init__(title=f"{APP_TITLE} {APP_VERSION}")
        self.set_default_size(820, 560)
        self.set_border_width(0)
        if APP_ICON_PATH.exists():
            self.set_icon_from_file(str(APP_ICON_PATH))

        self.power_path = None
        self.led_path = None
        self.controller_power_targets = {}
        self.config = load_config()
        self.language = self.config.get("language", DEFAULT_LANGUAGE)
        if self.language not in TRANSLATIONS:
            self.language = DEFAULT_LANGUAGE
        self.translated_widgets = {}
        self.indicator = None
        self.status_icon = None
        self.tray_menu = None
        self._build_css()
        self._build_ui()
        self._build_tray()
        self.refresh()
        GLib.timeout_add_seconds(POLL_SECONDS, self.refresh)

    def _build_css(self):
        css = b"""
        window { background: #f5f7f9; color: #1f2933; }
        .topbar { background: #17212b; color: #f8fafc; padding: 16px 20px; }
        .title { font-size: 22px; font-weight: 700; }
        .subtitle { color: #cbd5df; }
        .panel { background: #ffffff; border: 1px solid #d8dee6; border-radius: 8px; padding: 16px; }
        .section-title { font-size: 14px; font-weight: 700; color: #334155; }
        .status-ok { color: #087f5b; font-weight: 700; }
        .status-warn { color: #b7791f; font-weight: 700; }
        .status-bad { color: #c92a2a; font-weight: 700; }
        .metric { font-size: 32px; font-weight: 800; color: #111827; }
        .muted { color: #64748b; }
        textview { font-family: monospace; font-size: 12px; }
        button { min-height: 34px; }
        combobox, combobox button, combobox box {
            background: #ffffff;
            color: #1f2933;
        }
        combobox button:hover, combobox button:checked {
            background: #e8eef5;
            color: #111827;
        }
        combobox arrow {
            color: #1f2933;
        }
        menu, menuitem {
            background-color: #ffffff;
            color: #1f2933;
        }
        menuitem:hover {
            background-color: #e8eef5;
            color: #111827;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        topbar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        topbar.get_style_context().add_class("topbar")
        root.pack_start(topbar, False, False, 0)

        title = Gtk.Label(label=f"{APP_TITLE} {APP_VERSION}", xalign=0)
        title.get_style_context().add_class("title")
        topbar.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(label="Status, Akku und LED-Steuerung für xone-Geräte", xalign=0)
        subtitle.get_style_context().add_class("subtitle")
        topbar.pack_start(subtitle, False, False, 0)
        self.translated_widgets["subtitle"] = subtitle

        language_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        topbar.pack_start(language_row, False, False, 4)

        self.language_label = Gtk.Label(xalign=0)
        self.language_label.get_style_context().add_class("subtitle")
        language_row.pack_start(self.language_label, False, False, 0)

        self.language_combo = Gtk.ComboBoxText()
        for code, values in TRANSLATIONS.items():
            self.language_combo.append(code, values["language_name"])
        self.language_combo.set_active_id(self.language)
        self.language_combo.connect("changed", self.on_language_changed)
        language_row.pack_start(self.language_combo, False, False, 0)

        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        content.set_border_width(16)
        root.pack_start(content, True, True, 0)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.pack_start(left, True, True, 0)
        content.pack_start(right, True, True, 0)

        battery_panel = self._panel(left, "controller")
        self.device_label = Gtk.Label(xalign=0)
        self.device_label.set_line_wrap(True)
        battery_panel.pack_start(self.device_label, False, False, 0)

        self.battery_label = Gtk.Label(xalign=0)
        self.battery_label.get_style_context().add_class("metric")
        battery_panel.pack_start(self.battery_label, False, False, 6)

        self.battery_detail = Gtk.Label(xalign=0)
        self.battery_detail.get_style_context().add_class("muted")
        battery_panel.pack_start(self.battery_detail, False, False, 0)

        self.battery_bar = Gtk.LevelBar()
        self.battery_bar.set_min_value(0)
        self.battery_bar.set_max_value(100)
        battery_panel.pack_start(self.battery_bar, False, False, 10)

        power_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        battery_panel.pack_start(power_row, False, False, 0)

        self.controller_power_combo = Gtk.ComboBoxText()
        power_row.pack_start(self.controller_power_combo, True, True, 0)

        self.shutdown_controller_button = Gtk.Button()
        self.shutdown_controller_button.connect("clicked", self.on_shutdown_controller)
        power_row.pack_start(self.shutdown_controller_button, False, False, 0)

        led_panel = self._panel(left, "led")
        self.led_label = Gtk.Label(xalign=0)
        self.led_label.get_style_context().add_class("muted")
        led_panel.pack_start(self.led_label, False, False, 0)

        self.brightness = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 50, 1)
        self.brightness.set_draw_value(True)
        led_panel.pack_start(self.brightness, False, False, 8)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        led_panel.pack_start(controls, False, False, 0)

        self.mode_combo = Gtk.ComboBoxText()
        self.mode_options = [
            ("0", "mode_off"),
            ("1", "mode_on"),
            ("2", "mode_blink_fast"),
            ("3", "mode_blink_normal"),
            ("4", "mode_blink_slow"),
            ("8", "mode_fade_slow"),
            ("9", "mode_fade_fast"),
        ]
        for value, label_key in self.mode_options:
            self.mode_combo.append(value, tr(self.language, label_key))
        controls.pack_start(self.mode_combo, True, True, 0)

        self.save_led_button = Gtk.Button()
        self.save_led_button.connect("clicked", self.on_set_led)
        controls.pack_start(self.save_led_button, False, False, 0)

        status_panel = self._panel(right, "driver")
        self.driver_label = Gtk.Label(xalign=0)
        self.driver_label.set_line_wrap(True)
        status_panel.pack_start(self.driver_label, False, False, 0)

        action_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        status_panel.pack_start(action_row, False, False, 8)

        self.refresh_button = Gtk.Button()
        self.refresh_button.connect("clicked", lambda _button: self.refresh())
        action_row.pack_start(self.refresh_button, False, False, 0)

        self.reload_modules_button = Gtk.Button()
        self.reload_modules_button.connect("clicked", self.on_load_modules)
        action_row.pack_start(self.reload_modules_button, False, False, 0)

        log_panel = self._panel(right, "kernel_messages", expand=True)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        log_panel.pack_start(scroll, True, True, 0)

        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scroll.add(self.log_view)

        self.message = Gtk.Label(xalign=0)
        self.message.get_style_context().add_class("muted")
        root.pack_start(self.message, False, False, 10)
        self.apply_language()

    def _panel(self, parent, title_key, expand=False):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.get_style_context().add_class("panel")
        parent.pack_start(box, expand, expand, 0)

        label = Gtk.Label(xalign=0)
        label.get_style_context().add_class("section-title")
        box.pack_start(label, False, False, 0)
        self.translated_widgets[title_key] = label
        return box

    def apply_language(self):
        self.translated_widgets["subtitle"].set_text(tr(self.language, "subtitle"))
        self.language_label.set_text(f"{tr(self.language, 'language')}:")
        for key in ("controller", "led", "driver", "kernel_messages"):
            self.translated_widgets[key].set_text(tr(self.language, key))
        self.save_led_button.set_label(tr(self.language, "set_led"))
        self.shutdown_controller_button.set_label(tr(self.language, "shutdown_controller"))
        self.controller_power_combo.set_tooltip_text(tr(self.language, "controller_power"))
        self.shutdown_controller_button.set_tooltip_text(tr(self.language, "controller_power"))
        self.refresh_button.set_label(tr(self.language, "refresh"))
        self.reload_modules_button.set_label(tr(self.language, "load_modules"))
        if self.tray_menu:
            self.tray_status_item.set_label(f"{tr(self.language, 'tray_status')}: --")
            self.tray_battery_item.set_label(f"{tr(self.language, 'tray_battery')}: --")
            self.tray_show_item.set_label(tr(self.language, "tray_show"))
            self.tray_hide_item.set_label(tr(self.language, "tray_hide"))
            self.tray_power_item.set_label(tr(self.language, "tray_controller_power"))
            self.tray_refresh_item.set_label(tr(self.language, "refresh"))
            self.tray_quit_item.set_label(tr(self.language, "tray_quit"))

        active_mode = self.mode_combo.get_active_id()
        self.mode_combo.remove_all()
        for value, label_key in self.mode_options:
            self.mode_combo.append(value, tr(self.language, label_key))
        if active_mode is not None:
            self.mode_combo.set_active_id(active_mode)

    def on_language_changed(self, combo):
        selected = combo.get_active_id()
        if not selected or selected == self.language:
            return
        self.language = selected
        self.config["language"] = self.language
        save_config(self.config)
        self.apply_language()
        self.refresh()

    def _build_tray(self):
        self.tray_menu = Gtk.Menu()

        self.tray_status_item = Gtk.MenuItem()
        self.tray_status_item.set_sensitive(False)
        self.tray_menu.append(self.tray_status_item)

        self.tray_battery_item = Gtk.MenuItem()
        self.tray_battery_item.set_sensitive(False)
        self.tray_menu.append(self.tray_battery_item)

        self.tray_menu.append(Gtk.SeparatorMenuItem())

        self.tray_show_item = Gtk.MenuItem()
        self.tray_show_item.connect("activate", lambda _item: self.present())
        self.tray_menu.append(self.tray_show_item)

        self.tray_hide_item = Gtk.MenuItem()
        self.tray_hide_item.connect("activate", lambda _item: self.hide())
        self.tray_menu.append(self.tray_hide_item)

        self.tray_power_item = Gtk.MenuItem()
        self.tray_power_submenu = Gtk.Menu()
        self.tray_power_item.set_submenu(self.tray_power_submenu)
        self.tray_menu.append(self.tray_power_item)

        self.tray_refresh_item = Gtk.MenuItem()
        self.tray_refresh_item.connect("activate", lambda _item: self.refresh())
        self.tray_menu.append(self.tray_refresh_item)

        self.tray_menu.append(Gtk.SeparatorMenuItem())

        self.tray_quit_item = Gtk.MenuItem()
        self.tray_quit_item.connect("activate", lambda _item: Gtk.main_quit())
        self.tray_menu.append(self.tray_quit_item)

        self.tray_menu.show_all()
        self.apply_language()

        if AppIndicator:
            self.indicator = AppIndicator.Indicator.new(
                "xone-control",
                TRAY_CONNECTED_ICON,
                AppIndicator.IndicatorCategory.HARDWARE,
            )
            self.indicator.set_icon_theme_path(str(ICON_DIR))
            self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
            self.indicator.set_menu(self.tray_menu)
            return

        self.status_icon = Gtk.StatusIcon.new_from_icon_name("input-gaming")
        self.status_icon.set_visible(True)
        self.status_icon.connect("activate", self.on_tray_activate)
        self.status_icon.connect("popup-menu", self.on_tray_popup)

    def on_tray_activate(self, _status_icon):
        if self.is_visible():
            self.hide()
        else:
            self.present()

    def on_tray_popup(self, _status_icon, button, activate_time):
        self.tray_menu.popup(None, None, None, None, button, activate_time)

    def refresh(self):
        self._refresh_battery()
        self._refresh_controller_power()
        self._refresh_led()
        self._refresh_driver()
        self._refresh_logs()
        self._refresh_tray()
        return True

    def _battery_state(self):
        supplies = power_supplies()
        power_path = supplies[0] if supplies else None
        if not power_path:
            return {
                "connected": False,
                "model": "",
                "status": tr(self.language, "tray_disconnected"),
                "battery": "--",
            }

        model = read_text(power_path / "model_name", tr(self.language, "device_fallback"))
        level = read_text(power_path / "capacity_level", tr(self.language, "unknown"))
        capacity = read_text(power_path / "capacity")
        battery = f"{capacity}%" if capacity else level
        return {
            "connected": True,
            "model": model,
            "status": tr(self.language, "tray_connected"),
            "battery": battery,
        }

    def _refresh_tray(self):
        state = self._battery_state()
        label = state["battery"] if state["connected"] else "--"
        tooltip = tr(self.language, "tray_tooltip", status=state["status"], battery=state["battery"])
        if state["model"]:
            tooltip = f"{state['model']} · {tooltip}"

        self.tray_status_item.set_label(f"{tr(self.language, 'tray_status')}: {state['status']}")
        self.tray_battery_item.set_label(f"{tr(self.language, 'tray_battery')}: {state['battery']}")

        if self.indicator:
            self.indicator.set_icon_full(TRAY_CONNECTED_ICON if state["connected"] else TRAY_DISCONNECTED_ICON, tooltip)
            self.indicator.set_label(label, "")
        elif self.status_icon:
            if state["connected"] and TRAY_CONNECTED_ICON_PATH.exists():
                self.status_icon.set_from_file(str(TRAY_CONNECTED_ICON_PATH))
            elif TRAY_DISCONNECTED_ICON_PATH.exists():
                self.status_icon.set_from_file(str(TRAY_DISCONNECTED_ICON_PATH))
            else:
                self.status_icon.set_from_icon_name(TRAY_DISCONNECTED_ICON)
            self.status_icon.set_tooltip_text(tooltip)

    def _refresh_battery(self):
        supplies = power_supplies()
        self.power_path = supplies[0] if supplies else None
        if not self.power_path:
            self._set_device_status(tr(self.language, "no_controller"), "status-warn")
            self.battery_label.set_text("--")
            self.battery_detail.set_text(tr(self.language, "connect_controller"))
            self.battery_bar.set_value(0)
            return

        model = read_text(self.power_path / "model_name", tr(self.language, "device_fallback"))
        status = read_text(self.power_path / "status", tr(self.language, "unknown"))
        level = read_text(self.power_path / "capacity_level", tr(self.language, "unknown"))
        capacity = read_text(self.power_path / "capacity")

        self._set_device_status(tr(self.language, "connected", model=model), "status-ok")
        if capacity:
            self.battery_label.set_text(f"{capacity}%")
            self.battery_bar.set_value(float(capacity))
        else:
            self.battery_label.set_text(level)
            fallback = {"Critical": 8, "Low": 22, "Normal": 55, "High": 78, "Full": 100}
            self.battery_bar.set_value(fallback.get(level, 0))
        self.battery_detail.set_text(f"{status} · {self.power_path.name}")

    def _refresh_controller_power(self):
        active_id = self.controller_power_combo.get_active_id()
        targets = {}
        self.controller_power_combo.remove_all()

        for dongle in xone_dongles():
            for slot in active_client_slots(dongle):
                target_id = f"{dongle}:{slot}"
                label = tr(
                    self.language,
                    "controller_slot",
                    dongle=dongle.name,
                    slot=f"{slot:02d}",
                )
                targets[target_id] = {
                    "label": label,
                    "poweroff_path": dongle / "poweroff",
                    "slot": slot,
                }
                self.controller_power_combo.append(target_id, label)

        self.controller_power_targets = targets
        self._refresh_tray_power_menu()
        has_targets = bool(targets)
        self.controller_power_combo.set_sensitive(has_targets)
        self.shutdown_controller_button.set_sensitive(has_targets)

        if not has_targets:
            self.controller_power_combo.append("none", tr(self.language, "unavailable"))
            self.controller_power_combo.set_active_id("none")
            self.controller_power_combo.set_tooltip_text(tr(self.language, "no_shutdown_target"))
            return

        self.controller_power_combo.set_tooltip_text(tr(self.language, "controller_power"))
        if active_id in targets:
            self.controller_power_combo.set_active_id(active_id)
        else:
            self.controller_power_combo.set_active(0)

    def _refresh_tray_power_menu(self):
        if not self.tray_menu:
            return

        for item in self.tray_power_submenu.get_children():
            self.tray_power_submenu.remove(item)

        if not self.controller_power_targets:
            item = Gtk.MenuItem(label=tr(self.language, "unavailable"))
            item.set_sensitive(False)
            self.tray_power_submenu.append(item)
            self.tray_power_item.set_sensitive(False)
        else:
            self.tray_power_item.set_sensitive(True)
            for target_id, target in self.controller_power_targets.items():
                label = tr(self.language, "tray_power_off_controller", target=target["label"])
                item = Gtk.MenuItem(label=label)
                item.connect("activate", self.on_tray_shutdown_controller, target_id)
                self.tray_power_submenu.append(item)

        self.tray_power_submenu.show_all()

    def _set_device_status(self, text, style_class):
        context = self.device_label.get_style_context()
        for css_class in ("status-ok", "status-warn", "status-bad"):
            context.remove_class(css_class)
        context.add_class(style_class)
        self.device_label.set_text(text)

    def _refresh_led(self):
        leds = led_devices()
        self.led_path = leds[0] if leds else None
        if not self.led_path:
            self.led_label.set_text(tr(self.language, "no_led"))
            self.brightness.set_sensitive(False)
            self.mode_combo.set_sensitive(False)
            return

        self.brightness.set_sensitive(True)
        self.mode_combo.set_sensitive(True)
        brightness = read_text(self.led_path / "brightness", "0")
        max_brightness = read_text(self.led_path / "max_brightness", "50")
        mode = read_text(self.led_path / "mode", "0")
        self.led_label.set_text(
            tr(
                self.language,
                "brightness",
                device=self.led_path.name,
                brightness=brightness,
                max_brightness=max_brightness,
            )
        )
        self.brightness.set_range(0, int(max_brightness or 50))
        self.brightness.set_value(float(brightness or 0))
        self.mode_combo.set_active_id(mode)

    def _refresh_driver(self):
        modules = list_xone_modules()
        firmware = firmware_files()
        module_text = ", ".join(modules) if modules else tr(self.language, "no_modules")
        firmware_text = ", ".join(path.name for path in firmware) if firmware else tr(self.language, "no_firmware")
        self.driver_label.set_text(
            f"{tr(self.language, 'modules')}: {module_text}\n"
            f"{tr(self.language, 'firmware')}: {firmware_text}"
        )

    def _refresh_logs(self):
        log = run_text(["journalctl", "-k", "-n", "40", "--no-pager"])
        lines = [line for line in log.splitlines() if "xone" in line.lower() or "xbox" in line.lower()]
        buffer = self.log_view.get_buffer()
        buffer.set_text("\n".join(lines[-18:]) or tr(self.language, "no_kernel_messages"))

    def on_set_led(self, _button):
        if not self.led_path:
            self.message.set_text(tr(self.language, "no_led_short"))
            return

        brightness = int(self.brightness.get_value())
        mode = self.mode_combo.get_active_id()
        mode_ok, mode_msg = True, "ok"
        if mode is not None:
            mode_ok, mode_msg = write_sysfs(self.led_path / "mode", mode, self.language)

        brightness_ok, brightness_msg = write_sysfs(
            self.led_path / "brightness", brightness, self.language
        )

        applied_brightness = read_text(self.led_path / "brightness")
        applied_mode = read_text(self.led_path / "mode")
        applied = applied_brightness == str(brightness) and (mode is None or applied_mode == mode)
        if brightness_ok and mode_ok and applied:
            self.message.set_text(brightness_msg)
        elif brightness_ok and mode_ok:
            self.message.set_text(tr(self.language, "led_not_applied"))
        else:
            self.message.set_text(f"{mode_msg}; {brightness_msg}")
        self.refresh()

    def on_shutdown_controller(self, _button):
        target_id = self.controller_power_combo.get_active_id()
        self._shutdown_controller_target(target_id)

    def on_tray_shutdown_controller(self, _item, target_id):
        self._shutdown_controller_target(target_id)

    def _shutdown_controller_target(self, target_id):
        target = self.controller_power_targets.get(target_id)
        if not target:
            self.message.set_text(tr(self.language, "no_shutdown_target"))
            return

        ok, _message = write_sysfs(target["poweroff_path"], target["slot"], self.language)
        if ok:
            self.message.set_text(
                tr(self.language, "controller_shutdown_sent", target=target["label"])
            )
        else:
            self.message.set_text(tr(self.language, "controller_shutdown_failed"))
        self.refresh()

    def on_load_modules(self, _button):
        command = [
            "pkexec",
            "sh",
            "-c",
            "modprobe -r xpad mt76x2u 2>/dev/null || true; "
            "modprobe xone_gip xone_wired xone_dongle xone_gip_gamepad "
            "xone_gip_headset xone_gip_chatpad xone_gip_madcatz_strat "
            "xone_gip_madcatz_glam xone_gip_pdp_jaguar",
        ]
        try:
            subprocess.check_call(command)
            self.message.set_text(tr(self.language, "modules_loaded"))
        except FileNotFoundError:
            self.message.set_text(tr(self.language, "pkexec_missing"))
        except subprocess.CalledProcessError:
            self.message.set_text(tr(self.language, "modules_load_failed"))
        self.refresh()

    def on_delete_event(self, *_args):
        self.hide()
        return True


def main():
    lock_handle = acquire_single_instance_lock()
    if lock_handle is None:
        print("xone Control is already running.", file=sys.stderr)
        return 0

    start_hidden = "--hidden" in sys.argv[1:]
    window = XoneControl()
    window.connect("delete-event", window.on_delete_event)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    if start_hidden:
        GLib.idle_add(window.hide)
    Gtk.main()
    lock_handle.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
