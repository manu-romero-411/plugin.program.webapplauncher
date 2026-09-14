"""Entry point for the WebApp Launcher plugin, invoked by Kodi."""
from resources.lib.common import get_params
from resources.lib.router import route

if __name__ == "__main__":
    route(get_params())
