import logging
import time

from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.plugins as plugins
import pwnagotchi


BAT_DIR = "/sys/class/power_supply/rt5033-battery"
BAT_CAP = BAT_DIR + "/capacity"
BAT_STATUS = BAT_DIR + "/status"
BAT_VOLT = BAT_DIR + "/voltage_now"   # optional (µV)
BAT_CURR = BAT_DIR + "/current_now"   # optional (µA) may not exist


class PhoneBattery(plugins.Plugin):
    __author__ = "you"
    __version__ = "1.0"
    __license__ = "GPL3"
    __description__ = (
        "Phone battery indicator using /sys/class/power_supply/rt5033-battery. "
        "Shows percent, and optionally rotates between voltage/percent."
    )

    def __init__(self):
        self.ready = False

        # rotation like pisugarx
        self.drot = 0
        self.nextDChg = 0
        self.rotation_enabled = True
        self.default_display = "percentage"  # percentage | voltage

    def _read_text(self, path, default=None):
        try:
            with open(path, "r") as f:
                return f.read().strip()
        except Exception:
            return default

    def _read_int(self, path, default=None):
        v = self._read_text(path, None)
        if v is None:
            return default
        try:
            return int(v)
        except Exception:
            return default

    def _get_capacity(self):
        cap = self._read_int(BAT_CAP, None)
        if cap is None:
            return None
        # clamp to sane values
        if cap < 0:
            cap = 0
        if cap > 100:
            cap = 100
        return cap

    def _get_status(self):
        return self._read_text(BAT_STATUS, "Unknown")

    def _get_voltage(self):
        # voltage_now is in microvolts
        uv = self._read_int(BAT_VOLT, None)
        if uv is None:
            return None
        return uv / 1_000_000.0

    def on_loaded(self):
        logging.info("[PhoneBattery] plugin loaded.")
        # Optional config (same pattern as your example):
        # main:
        #   plugins:
        #     phonebattery:
        #       rotation: true
        #       default_display: percentage
        try:
            cfg = pwnagotchi.config['main']['plugins'].get('phonebattery', {})
            self.rotation_enabled = cfg.get('rotation', True)
            self.default_display = cfg.get('default_display', 'percentage').lower()
        except Exception:
            pass

        valid = ['percentage', 'percent', 'voltage']
        if self.default_display not in valid:
            self.default_display = 'percentage'

    def on_ready(self, agent):
        # sysfs exists? then we're "ready"
        self.ready = (self._get_capacity() is not None)

    def on_ui_setup(self, ui):
        ui.add_element(
            "bat",
            LabeledValue(
                color=BLACK,
                label="BAT",
                value="--%",
                position=(ui.width() / 2 + 15, 0),
                label_font=fonts.Bold,
                text_font=fonts.Medium,
            ),
        )

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element("bat")

    def on_ui_update(self, ui):
        # guard
        if 'bat' not in ui._state._state:
            return

        cap = self._get_capacity()
        status = self._get_status()
        volt = self._get_voltage()

        self.ready = (cap is not None)

        if not self.ready:
            ui._state._state['bat'].label = "BAT"
            ui.set('bat', "--%")
            return

        # plugged/charging detection:
        # status examples: Charging, Discharging, Full, Not charging, Unknown
        charging = str(status).lower().startswith("charg")
        full = str(status).lower().startswith("full")
        plugged = charging or full or (str(status).lower() == "not charging")

        ui._state._state['bat'].label = "CHG" if plugged else "BAT"

        # rotation/default display logic
        if self.rotation_enabled:
            if time.time() > self.nextDChg:
                # rotate between voltage and percentage
                self.drot = (self.drot + 1) % 2
                self.nextDChg = time.time() + 5

            if self.drot == 0:
                # voltage if available, else percent
                if volt is not None:
                    ui.set('bat', f"{volt:.2f}V")
                else:
                    ui.set('bat', f"{cap:.0f}%")
            else:
                ui.set('bat', f"{cap:.0f}%")
        else:
            if self.default_display in ['percentage', 'percent']:
                ui.set('bat', f"{cap:.0f}%")
            else:
                if volt is not None:
                    ui.set('bat', f"{volt:.2f}V")
                else:
                    ui.set('bat', f"{cap:.0f}%")
