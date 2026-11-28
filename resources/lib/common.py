"""Kodi's side of the add-on: its settings, texts, log and plugin URLs."""
from __future__ import annotations

import os
import sys
from urllib.parse import parse_qsl, urlencode

import xbmc
import xbmcaddon

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo("id")


def get_params() -> dict[str, str]:
    """The query of the URL Kodi called the plugin with (sys.argv[2])."""
    query = sys.argv[2] if len(sys.argv) > 2 else ""
    return dict(parse_qsl(query.lstrip("?")))


def handle() -> int:
    """The plugin handle Kodi passed (sys.argv[1]); -1 when run as a script."""
    try:
        return int(sys.argv[1])
    except (IndexError, ValueError):
        return -1


def plugin_url(**query: str) -> str:
    """This plugin's URL with that query."""
    return f"plugin://{ADDON_ID}/?{urlencode(query)}"


def text(string_id: int) -> str:
    """A text of strings.po, in Kodi's language."""
    return ADDON.getLocalizedString(string_id)


def log(message: str, level: int = xbmc.LOGINFO) -> None:
    """A line in Kodi's log, marked with the add-on's id."""
    xbmc.log(f"[{ADDON_ID}] {message}", level)


def warn(message: str) -> None:
    """A warning in Kodi's log."""
    log(message, xbmc.LOGWARNING)


def setting_string(setting: str) -> str:
    """A text setting, without surrounding spaces."""
    return ADDON.getSettingString(setting).strip()


def setting_path(setting: str) -> str:
    """A path setting, with a leading ``~`` expanded (Kodi does not)."""
    return os.path.expanduser(setting_string(setting))


def setting_bool(setting: str) -> bool:
    """A boolean setting."""
    return ADDON.getSettingBool(setting)
