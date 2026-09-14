#!/usr/bin/env bash
# Example global executor script for the WebApp Launcher Kodi add-on.
#
# Used only for .webapp files that do NOT define custom_command. Kodi
# calls it as:
#   run-webapp.sh /path/to/launchers/my_app.webapp
#
# This example reads the [kodi_webapp] "url" field with awk and opens it
# in a Firefox app window. Real .webapp files look like:
#   [kodi_webapp]
#   name=YouTube
#   url=https://www.youtube.com
set -euo pipefail

webapp_file="$1"

if [[ ! -f "$webapp_file" ]]; then
    echo "webapp file not found: $webapp_file" >&2
    exit 1
fi

url=$(awk -F'=' '/^[Uu][Rr][Ll][[:space:]]*=/{ $1=""; sub(/^[= ]+/, ""); print; exit }' "$webapp_file")

if [[ -z "$url" ]]; then
    echo "no url= field found in $webapp_file" >&2
    exit 1
fi

# --app opens the page without browser chrome, close to a native window.
exec firefox --new-window "$url"
