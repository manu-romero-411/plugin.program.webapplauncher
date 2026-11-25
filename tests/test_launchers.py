"""Tests of resources/lib/launchers.py, which runs without Kodi:
python3 -m unittest discover tests"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "resources", "lib"))

import launchers  # pylint: disable=import-error,wrong-import-position


class LauncherTest(unittest.TestCase):
    """Reading .webapp files, their art and their commands."""

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.warnings = []

    def write(self, name, content):
        """A file of the launchers folder."""
        path = os.path.join(self.folder, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path

    def scan(self, **options):
        """The folder's launchers, warnings kept."""
        return launchers.scan(self.folder, warn=self.warnings.append, **options)

    def test_valid_launchers_are_listed_by_label(self):
        """Valid .webapp files are listed, sorted by label; other files are not."""
        self.write("youtube.webapp", "[kodi_webapp]\nname=YouTube\nurl=https://www.youtube.com\n")
        self.write("my_cool_app.webapp", "[KODI_WEBAPP]\n url = https://example.org \n")
        self.write("notes.txt", "[kodi_webapp]\nurl=x\n")
        found = self.scan()
        self.assertEqual([launcher.label for launcher in found], ["My Cool App", "YouTube"])
        self.assertEqual(found[0].key, "my_cool_app")
        self.assertEqual(found[0].url, "https://example.org")

    def test_labels_are_file_names_when_not_prettified(self):
        """Without prettifying, a nameless launcher shows its file name."""
        self.write("my_cool_app.webapp", "[kodi_webapp]\nurl=https://example.org\n")
        self.assertEqual(self.scan(prettify_labels=False)[0].label, "my_cool_app")

    def test_files_without_url_section_or_ini_are_skipped(self):
        """No url, no [kodi_webapp] or no ini: skipped, not breaking the rest."""
        self.write("no_url.webapp", "[kodi_webapp]\nname=Nothing\n")
        self.write("empty_url.webapp", "[kodi_webapp]\nurl=\n")
        self.write("other.webapp", "[desktop]\nurl=https://example.org\n")
        self.write("broken.webapp", "url=https://example.org\n")
        self.assertEqual(self.scan(), [])
        self.assertEqual(len(self.warnings), 2)  # the missing url is silent

    def test_art_is_found_by_file_name_in_order(self):
        """The cover is found by file name, .png before .jpg."""
        self.write("youtube.webapp", "[kodi_webapp]\nurl=https://www.youtube.com\n")
        jpg = self.write("app-icons/youtube.jpg", "")
        self.assertEqual(self.scan()[0].art, jpg)
        png = self.write("app-icons/youtube.png", "")
        self.assertEqual(self.scan()[0].art, png)
        self.assertIsNone(self.scan(icons_subfolder="covers")[0].art)

    def test_find_takes_only_names_of_the_folder(self):
        """A key can't reach outside the launchers folder."""
        self.write("youtube.webapp", "[kodi_webapp]\nurl=https://www.youtube.com\n")
        self.assertEqual(launchers.find(self.folder, "youtube").url, "https://www.youtube.com")
        self.assertIsNone(launchers.find(self.folder, "missing"))
        self.assertIsNone(launchers.find(self.folder, "../youtube"))
        self.assertIsNone(launchers.find(self.folder, ""))

    def test_custom_command_tokens_and_quotes(self):
        """custom_command is split like a shell would, tokens replaced in each argument."""
        path = self.write("a b.webapp", '[kodi_webapp]\nurl=https://example.org/a b\n'
                          'custom_command="/opt/my app/launcher.sh" '
                          '--file %WEBAPP% --url="%URL%"\n')
        launcher = launchers.find(self.folder, "a b")
        self.assertEqual(launchers.command(launcher, "/unused.sh"),
                         ["/opt/my app/launcher.sh", "--file", path,
                          "--url=https://example.org/a b"])

    def test_the_executor_script_takes_the_file(self):
        """Without custom_command the executor script gets the .webapp file."""
        path = self.write("youtube.webapp", "[kodi_webapp]\nurl=https://www.youtube.com\n")
        launcher = launchers.find(self.folder, "youtube")
        self.assertEqual(launchers.command(launcher, "/home/me/run-webapp.sh"),
                         ["/home/me/run-webapp.sh", path])
        with self.assertRaises(ValueError):
            launchers.command(launcher, "")

    def test_a_broken_custom_command_is_refused(self):
        """An unclosed quote in custom_command is an error, not a guess."""
        self.write("bad.webapp", '[kodi_webapp]\nurl=x\ncustom_command="/opt/unclosed\n')
        with self.assertRaises(ValueError):
            launchers.command(launchers.find(self.folder, "bad"), "/run.sh")

    def test_prettify(self):
        """File names become titles."""
        self.assertEqual(launchers.prettify("my_cool-app"), "My Cool App")
        self.assertEqual(launchers.prettify("tv"), "Tv")


if __name__ == "__main__":
    unittest.main()
