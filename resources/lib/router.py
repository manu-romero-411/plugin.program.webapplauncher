"""What the plugin does for each URL Kodi calls it with.

* no action: the menu of launchers (asking for the launchers folder first if
  none is configured);
* ``action=run&name=<key>``: run the launcher of ``<key>.webapp`` (the
  stable URL for favourites and skin shortcuts);
* ``action=settings``: open the add-on's settings.
"""
from __future__ import annotations

import os

import xbmcgui
import xbmcplugin

from . import launchers, runner
from .common import (ADDON, handle, log, plugin_url, setting_bool, setting_string,
                     text, warn)

ICON = os.path.join(ADDON.getAddonInfo("path"), "icon.png")
FANART = os.path.join(ADDON.getAddonInfo("path"), "fanart.jpg")


def notify(message: str, error: bool = False) -> None:
    """A Kodi notification with the add-on's name."""
    icon = xbmcgui.NOTIFICATION_ERROR if error else ICON
    xbmcgui.Dialog().notification(ADDON.getAddonInfo("name"), message, icon, 5000)


def launchers_folder(ask: bool) -> str:
    """The configured launchers folder; when there is none and ``ask``, the
    one the user picks now (saved in the settings)."""
    folder = setting_string("launchers_folder")
    if folder or not ask:
        return folder
    folder = xbmcgui.Dialog().browseSingle(0, text(30021), "files")
    if folder:
        ADDON.setSettingString("launchers_folder", folder)
    return folder or ""


def scan_options() -> dict:
    """The settings scanning takes."""
    return {"icons_subfolder": setting_string("icons_subfolder"),
            "prettify_labels": setting_bool("prettify_labels"), "warn": warn}


def settings_item() -> None:
    """A menu entry that opens the add-on's settings."""
    item = xbmcgui.ListItem(text(30027))
    item.setArt({"icon": ICON, "thumb": ICON, "fanart": FANART})
    xbmcplugin.addDirectoryItem(handle(), plugin_url(action="settings"), item, isFolder=False)


def list_launchers() -> None:
    """The menu: one entry per valid launcher, each runnable, so Kodi's own
    context menu adds it to the favourites."""
    plugin = handle()
    xbmcplugin.setContent(plugin, "files")
    folder = launchers_folder(ask=True)
    entries = []
    if not folder:
        notify(text(30020), error=True)
    elif not os.path.isdir(folder):
        notify(f"{text(30026)}: {folder}", error=True)
    else:
        entries = launchers.scan(folder, **scan_options())
        if not entries:
            notify(text(30023))
    for launcher in entries:
        item = xbmcgui.ListItem(launcher.label)
        art = launcher.art or ICON
        item.setArt({"poster": art, "thumb": art, "icon": art, "fanart": FANART})
        tag = item.getVideoInfoTag()
        tag.setTitle(launcher.label)
        tag.setPlot(launcher.url)
        item.addContextMenuItems([(text(30027), f"Addon.OpenSettings({ADDON.getAddonInfo('id')})")])
        xbmcplugin.addDirectoryItem(plugin, plugin_url(action="run", name=launcher.key), item,
                                    isFolder=False)
    if not entries:
        settings_item()
    xbmcplugin.addSortMethod(plugin, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(plugin, cacheToDisc=False)


def run_launcher(key: str) -> None:
    """Run the launcher of ``<key>.webapp``."""
    folder = launchers_folder(ask=False)
    launcher = launchers.find(folder, key, **scan_options()) if folder else None
    if launcher is None:
        notify(text(30024) % key, error=True)
        return
    try:
        arguments = launchers.command(launcher, setting_string("executor_script"))
    except ValueError as error:
        warn(str(error))
        notify(text(30022) if not launcher.custom_command else text(30025) % launcher.label,
               error=True)
        return
    notify(f"{text(30028)} {launcher.label}")
    if not runner.run(arguments, setting_bool("minimize_on_launch"), setting_bool("wait_for_exit")):
        notify(text(30025) % launcher.label, error=True)


def route(params: dict[str, str]) -> None:
    """Do what the URL's query asks."""
    action = params.get("action", "")
    log(f"called with {params!r}")
    if action == "run":
        run_launcher(params.get("name", ""))
    elif action == "settings":
        ADDON.openSettings()
    else:
        list_launchers()
