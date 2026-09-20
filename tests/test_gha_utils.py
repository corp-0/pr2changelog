import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from pr2changelog.gha_utils import (
    gha_debug, gha_error, gha_notice, gha_print, gha_set_output,
    gha_warning, gha_write_summary_line, gha_write_to_summary,
)


class GhaUtilsTest(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)
        self.output = self.directory / "output file"
        self.summary = self.directory / "summary file"
        environment = mock.patch.dict(os.environ, {
            "GITHUB_OUTPUT": str(self.output),
            "GITHUB_STEP_SUMMARY": str(self.summary),
        }, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def test_outputs_preserve_values_and_append_without_logging(self):
        values = ["1", "", "# Changelog\n\n* café: 100% done\nEOF\n",
                  '"quotes" $HOME $(echo command) `echo command` \\path',
                  "first\r\nsecond"]
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            for index, value in enumerate(values):
                gha_set_output(f"output_{index}", value)

        self.assertEqual("", stdout.getvalue())
        remaining = self.output.read_bytes().decode("utf-8")
        for index, value in enumerate(values):
            header, remaining = remaining.split("\n", 1)
            name, delimiter = header.split("<<", 1)
            actual, remaining = remaining.split(f"\n{delimiter}\n", 1)
            self.assertEqual(f"output_{index}", name)
            self.assertEqual(value, actual)
        self.assertEqual("", remaining)

    def test_numeric_output(self):
        gha_set_output("found_changes", 0)
        self.assertIn("\n0\n", self.output.read_text())

    def test_invalid_output_names(self):
        for name in ("", "a\nb", "a\rb", "a=b", "a<<b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                gha_set_output(name, "value")
        self.assertFalse(self.output.exists())

    @mock.patch("pr2changelog.gha_utils.uuid4", return_value="collision")
    def test_output_delimiter_collision_is_rejected(self, uuid):
        with self.assertRaises(ValueError):
            gha_set_output("content", "text\nghadelimiter_collision\ninjected=value")
        self.assertFalse(self.output.exists())

    def test_output_requires_runner_file(self):
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaises(KeyError):
            gha_set_output("content", "value")

    def test_annotations_escape_data_and_print_once(self):
        for function, command in ((gha_debug, "debug"), (gha_warning, "warning"),
                                  (gha_error, "error")):
            with self.subTest(command=command):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    function("100%\r\n::error::injected")
                self.assertEqual(f"::{command}::100%25%0D%0A::error::injected\n",
                                 stdout.getvalue())

    def test_info_prints_once(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            gha_print("hello")
        self.assertEqual("hello\n", stdout.getvalue())

    def test_notice_escapes_properties_and_data(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            gha_notice("path:with,comma%\r\n", 2, 4, "title:,\n", "body%\nnext")
        self.assertEqual(
            "::notice file=path%3Awith%2Ccomma%25%0D%0A,line=2,endLine=4,"
            "title=title%3A%2C%0A::body%25%0Anext\n", stdout.getvalue())

    def test_summary_appends_and_replaces_whole_document(self):
        gha_write_summary_line("old")
        gha_write_to_summary("# New\n\ncafé", append=False)
        gha_write_summary_line("last")
        self.assertEqual("# New\n\ncafé\nlast\n", self.summary.read_text())

    def test_summary_line_can_replace(self):
        gha_write_summary_line("old")
        gha_write_summary_line("new", append=False)
        self.assertEqual("new\n", self.summary.read_text())

    def test_helpers_do_not_execute_shell_text(self):
        marker = self.directory / "executed"
        message = f'" $(touch {marker}) `touch {marker}` $HOME'
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            gha_debug(message)
            gha_notice(message, 1, 1, message, message)
            gha_set_output("content", message)
            gha_write_to_summary(message)
        self.assertFalse(marker.exists())
        self.assertIn(message, stdout.getvalue())
        self.assertIn(message, self.output.read_text())
        self.assertEqual(message + "\n", self.summary.read_text())
