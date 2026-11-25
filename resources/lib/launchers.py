"""The .webapp launcher files: reading them, their cover art and the command
that runs each one.

Nothing here talks to Kodi, so it can be tested outside it: warnings about
files that are skipped go to the ``warn`` callback the caller passes.
"""
from __future__ import annotations

import configparser
import os
import shlex
from dataclasses import dataclass
from typing import Callable, Optional

SECTION = "kodi_webapp"
EXTENSION = ".webapp"
ART_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


@dataclass(frozen=True)
class Launcher:
    """A launcher: its stable key (the file name without .webapp), what the
    menu shows, its file, its url, its own command if any, and its cover."""

    key: str
    label: str
    path: str
    url: str
    custom_command: str = ""
    art: Optional[str] = None


def prettify(key: str) -> str:
    """Turn a file name such as my_cool_app into "My Cool App"."""
    words = key.replace("_", " ").replace("-", " ").split()
    return " ".join(word[:1].upper() + word[1:] for word in words) or key


def find_art(folder: str, icons_subfolder: str, key: str) -> Optional[str]:
    """The cover of ``key`` in the icons subfolder, by file name, trying
    .png, .jpg, .jpeg and .webp in that order."""
    if not icons_subfolder:
        return None
    for extension in ART_EXTENSIONS:
        candidate = os.path.join(folder, icons_subfolder, key + extension)
        if os.path.isfile(candidate):
            return candidate
    return None


def read_launcher(path: str, prettify_labels: bool = True,
                  warn: Callable[[str], None] = lambda message: None) -> Optional[Launcher]:
    """The launcher of a .webapp file, or None when it is not one: not an
    ini file, no [kodi_webapp] section (any case), or no url (silently)."""
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        with open(path, encoding="utf-8") as handle:
            parser.read_file(handle)
    except (OSError, UnicodeDecodeError, configparser.Error) as error:
        warn(f"skipping {path}: not a valid ini file ({error})")
        return None
    section = next((name for name in parser.sections() if name.lower() == SECTION), None)
    if section is None:
        warn(f"skipping {path}: no [{SECTION}] section")
        return None
    values = parser[section]
    url = values.get("url", "").strip()
    if not url:
        return None
    key = os.path.basename(path)[:-len(EXTENSION)]
    label = values.get("name", "").strip() or (prettify(key) if prettify_labels else key)
    return Launcher(key=key, label=label, path=os.path.abspath(path), url=url,
                    custom_command=values.get("custom_command", "").strip())


def scan(folder: str, icons_subfolder: str = "app-icons", prettify_labels: bool = True,
         warn: Callable[[str], None] = lambda message: None) -> list[Launcher]:
    """The valid launchers of a folder, sorted by label (case-insensitive)."""
    found = []
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if not name.lower().endswith(EXTENSION) or not os.path.isfile(path):
            continue
        launcher = read_launcher(path, prettify_labels, warn)
        if launcher is not None:
            art = find_art(folder, icons_subfolder, launcher.key)
            found.append(Launcher(**{**launcher.__dict__, "art": art}))
    return sorted(found, key=lambda launcher: (launcher.label.casefold(), launcher.key))


def find(folder: str, key: str, icons_subfolder: str = "app-icons",
         prettify_labels: bool = True,
         warn: Callable[[str], None] = lambda message: None) -> Optional[Launcher]:
    """The launcher whose file is ``<key>.webapp`` in the folder, if valid."""
    if not key or os.sep in key or key in (".", ".."):
        return None
    path = os.path.join(folder, key + EXTENSION)
    if not os.path.isfile(path):
        return None
    launcher = read_launcher(path, prettify_labels, warn)
    if launcher is None:
        return None
    return Launcher(**{**launcher.__dict__, "art": find_art(folder, icons_subfolder, key)})


def command(launcher: Launcher, executor_script: str) -> list[str]:
    """The command line that runs a launcher.

    Its own ``custom_command``, split like a shell would (quotes respected),
    with %WEBAPP% and %URL% replaced in every argument; else the executor
    script with the .webapp file as its only argument.

    Raises:
        ValueError: no custom_command and no executor script, or a
            custom_command that cannot be split (an unclosed quote).
    """
    if launcher.custom_command:
        try:
            arguments = shlex.split(launcher.custom_command)
        except ValueError as error:
            raise ValueError(f"bad custom_command in {launcher.path}: {error}") from error
        if not arguments:
            raise ValueError(f"empty custom_command in {launcher.path}")
        return [argument.replace("%WEBAPP%", launcher.path).replace("%URL%", launcher.url)
                for argument in arguments]
    if not executor_script:
        raise ValueError("no executor script configured")
    return [executor_script, launcher.path]
