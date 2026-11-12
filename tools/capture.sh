#!/usr/bin/env bash
# Capture the settings screens the guide tells a person to walk through, straight from the device.
#
# Opened by intent rather than by tapping: the coordinates differ between phones and OS versions,
# but these action names are stable, and a screenshot of the right screen is worth more than a
# screenshot of whichever screen a coordinate happened to hit.
set -u
SER="${SER:-emulator-5554}"
OUT="${OUT:-$(cd "$(dirname "$0")/.." && pwd)/docs/guide/shots}"
mkdir -p "$OUT"

shot() {                      # shot <name> <wait-seconds>
  sleep "${2:-3}"
  adb -s "$SER" exec-out screencap -p > "$OUT/$1.png"
  printf '%-28s %s bytes\n' "$1" "$(stat -c%s "$OUT/$1.png")"
}

open() { adb -s "$SER" shell am start -a "$1" >/dev/null 2>&1; }

# --- Developer options ------------------------------------------------------
open android.settings.DEVICE_INFO_SETTINGS
shot 01-about-phone 4

open android.settings.APPLICATION_DEVELOPMENT_SETTINGS
shot 02-developer-options 4

# --- The toggles the app needs ---------------------------------------------
open android.settings.MANAGE_UNKNOWN_APP_SOURCES
shot 03-install-unknown-apps 4

open android.settings.IGNORE_BATTERY_OPTIMIZATION_SETTINGS
shot 04-battery-optimization 4

open android.settings.NOTIFICATION_SETTINGS
shot 05-notifications 3

# --- Wireless debugging is the sane way in on a phone ----------------------
open android.settings.APPLICATION_DEVELOPMENT_SETTINGS
shot 06-dev-options-root 3
