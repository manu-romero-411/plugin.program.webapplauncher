"""Running a launcher's command.

Inside Kodi's Flatpak (tv.kodi.Kodi) programs and scripts of the system are
not reachable: the command then runs on the host through ``flatpak-spawn
--host``, which needs the Flatpak to be allowed to talk to
org.freedesktop.Flatpak (flatpak override --user
--talk-name=org.freedesktop.Flatpak tv.kodi.Kodi).
"""
from __future__ import annotations

import os
import subprocess

import xbmc

from .common import log, warn

FLATPAK_INFO = "/.flatpak-info"


def in_flatpak() -> bool:
    """Whether Kodi runs in a Flatpak sandbox."""
    return os.path.exists(FLATPAK_INFO)


def host_command(arguments: list[str]) -> list[str]:
    """The command, run on the host when Kodi is in a Flatpak."""
    if in_flatpak():
        return ["flatpak-spawn", "--host", *arguments]
    return arguments


def run(arguments: list[str], minimize: bool, wait: bool) -> bool:
    """Start the command (after minimizing Kodi, if asked) and, if asked,
    wait for it to end. Whether it could be started (and, when waited for,
    ended with 0)."""
    arguments = host_command(arguments)
    log(f"running: {arguments!r}")
    if minimize:
        xbmc.executebuiltin("Minimize")
    try:
        # its own session, so that it outlives the plugin's process
        with subprocess.Popen(arguments, stdin=subprocess.DEVNULL, start_new_session=True,
                              close_fds=True) as process:
            if not wait:
                return True
            status = process.wait()
    except OSError as error:
        warn(f"cannot run {arguments[0]}: {error}")
        return False
    if status != 0:
        warn(f"{arguments!r} ended with status {status}")
    return status == 0
