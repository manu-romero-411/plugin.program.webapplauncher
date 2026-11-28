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


GRACE_SECONDS = 2.0

# Run on the host, after the command has ended: brings Kodi's window back.
# Wayland (wlroots compositors, such as labwc) through wlrctl; X11 through
# xdotool or wmctrl. The first one found that works wins.
RESTORE_SCRIPT = """
"$@"
status=$?
have() { command -v "$1" >/dev/null 2>&1; }
if [ -n "$WAYLAND_DISPLAY" ] && have wlrctl; then
    for id in Kodi kodi tv.kodi.Kodi; do
        wlrctl toplevel focus "app_id:$id" 2>/dev/null && exit "$status"
    done
fi
if [ -n "$DISPLAY" ]; then
    if have xdotool; then
        xdotool search --onlyvisible --class kodi windowactivate 2>/dev/null \\
            || xdotool search --class kodi windowmap windowactivate 2>/dev/null \\
            && exit "$status"
    fi
    if have wmctrl; then
        wmctrl -x -a kodi 2>/dev/null && exit "$status"
    fi
fi
exit "$status"
"""


def with_restore(arguments: list[str]) -> list[str]:
    """The command, followed on the host by bringing Kodi's window back."""
    return ["sh", "-c", RESTORE_SCRIPT, "sh", *arguments]


def run(arguments: list[str], minimize: bool, wait: bool) -> bool:
    """Start the command and, if asked, wait for it to end. Kodi is minimized
    (if asked) only once the command has survived a moment, so that a command
    which cannot even start does not leave a black screen behind. Whether it
    could be started (and, when waited for, ended with 0)."""
    log(f"running: {arguments!r}")
    arguments = host_command(with_restore(arguments) if minimize else arguments)
    try:
        # its own session, so that it outlives the plugin's process. Not used as
        # a context manager: leaving that would wait for the command to end,
        # whatever "wait" says.
        # pylint: disable-next=consider-using-with
        process = subprocess.Popen(arguments, stdin=subprocess.DEVNULL, start_new_session=True,
                                   close_fds=True)
        try:
            status = process.wait(timeout=GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            if minimize:
                xbmc.executebuiltin("Minimize")
            if not wait:
                return True
            status = process.wait()
        else:
            if status == 0 and minimize:
                xbmc.executebuiltin("Minimize")
    except OSError as error:
        warn(f"cannot run {arguments[0]}: {error}")
        return False
    if status != 0:
        warn(f"{arguments!r} ended with status {status}")
    return status == 0
