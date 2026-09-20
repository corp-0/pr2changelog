import io
import json
import os
import tempfile
import traceback
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import main
import requests

from pr2changelog.exceptions import ApiError


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)
        self.changelog = self.directory / "CHANGELOG.md"
        self.output = self.directory / "output"
        environment = mock.patch.dict(os.environ, {
            "GITHUB_EVENT_PATH": "tests/data/merged.json",
            "GITHUB_OUTPUT": str(self.output),
            "INPUT_FILE_NAME": str(self.changelog),
        }, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def read_outputs(self):
        remaining = self.output.read_text()
        outputs = {}
        while remaining:
            header, remaining = remaining.split("\n", 1)
            name, delimiter = header.split("<<", 1)
            outputs[name], remaining = remaining.split(f"\n{delimiter}\n", 1)
        return outputs

    def test_default_options(self):
        main.main()
        outputs = self.read_outputs()
        self.assertEqual("0", outputs["skip_changelog"])
        self.assertEqual("1", outputs["found_changes"])
        self.assertEqual("1", outputs["generated_changelog"])
        self.assertEqual(self.changelog.read_text(), outputs["changelog_content"])
        self.assertIn("fixed shit.", outputs["changelog_content"])

    @mock.patch.dict(os.environ, {"INPUT_CATEGORIES": "Fix;New;Improvement"})
    def test_with_categories(self):
        main.main()
        content = self.read_outputs()["changelog_content"]
        self.assertEqual(self.changelog.read_text(), content)
        for category in ("Fix", "New", "Improvement"):
            self.assertIn(f"**[{category}]**", content)

    @mock.patch.dict(os.environ, {"INPUT_CHANGE_TOKEN": "NO_CHANGES"})
    def test_without_changes(self):
        main.main()
        self.assertEqual({"skip_changelog": "0", "found_changes": "0", "generated_changelog": "0"},
                         self.read_outputs())
        self.assertFalse(self.changelog.exists())

    @mock.patch("pr2changelog.api_caller.requests.post")
    @mock.patch.dict(os.environ, {
        "INPUT_API_URL": "https://example.com/changelog",
        "INPUT_API_SECRET_TOKEN": "test-secret",
        "INPUT_CATEGORIES": "Fix;New;Improvement",
    })
    def test_skips_file_and_api_without_missing_changes_warning(self, post):
        for body_fields in ({"body": "[NOCL]"}, {"body": "CL: [Fix] ignored change\n[NOCL]"},
                            {"body": "CL: [Wrong] ignored invalid category\n[NOCL]"},
                            {}, {"body": None}, {"body": ""}, {"body": "\r\n\t "}):
            for existing_file in (False, True):
                with self.subTest(body_fields=body_fields, existing_file=existing_file):
                    self.changelog.unlink(missing_ok=True)
                    if existing_file:
                        self.changelog.write_text("Existing changelog\n")
                    self.output.write_text("")
                    payload = json.loads(Path("tests/data/merged.json").read_text())
                    payload["pull_request"].pop("body", None)
                    payload["pull_request"].update(body_fields)
                    event = self.directory / "event.json"
                    event.write_text(json.dumps(payload))
                    stdout = io.StringIO()
                    with mock.patch.dict(os.environ, {"GITHUB_EVENT_PATH": str(event)}), redirect_stdout(stdout):
                        main.main()
                    self.assertEqual({
                        "skip_changelog": "1",
                        "found_changes": "0",
                        "generated_changelog": "0",
                        "changelog_content": "",
                    }, self.read_outputs())
                    self.assertNotIn("::warning::", stdout.getvalue())
                    self.assertNotIn("::error::", stdout.getvalue())
                    if not (body_fields.get("body") or "").strip():
                        self.assertIn("PR body is empty: skipping changelog generation", stdout.getvalue())
                        self.assertNotIn("[NOCL] found", stdout.getvalue())
                    self.assertEqual(existing_file, self.changelog.exists())
                    if existing_file:
                        self.assertEqual("Existing changelog\n", self.changelog.read_text())
                    post.assert_not_called()

    @mock.patch("pr2changelog.api_caller.requests.post")
    @mock.patch.dict(os.environ, {
        "INPUT_API_URL": "https://example.com/changelog",
        "INPUT_API_SECRET_TOKEN": "test-secret",
        "INPUT_WRITE_TO_FILE": "false",
    })
    def test_api_only(self, post):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            main.main()
        self.assertIn("::debug::Post data:", stdout.getvalue())
        self.assertIn("'category': 'FIX'", stdout.getvalue())
        self.assertNotIn("'secret_token':", stdout.getvalue())
        self.assertNotIn("test-secret", stdout.getvalue())
        self.assertIn("Found API URL: ***", stdout.getvalue())
        self.assertNotIn("https://example.com/changelog", stdout.getvalue())
        self.assertEqual(3, post.call_count)
        self.assertEqual("https://example.com/changelog", post.call_args.args[0])
        self.assertEqual("test-secret", post.call_args.kwargs["data"]["secret_token"])
        self.assertEqual("1", self.read_outputs()["generated_changelog"])
        self.assertIn("fixed shit.", self.read_outputs()["changelog_content"])
        self.assertFalse(self.changelog.exists())

    @mock.patch.dict(os.environ, {
        "INPUT_API_URL": "https://private-api.example/register-change",
        "INPUT_API_SECRET_TOKEN": "test-secret",
        "INPUT_WRITE_TO_FILE": "false",
    })
    def test_api_failures_do_not_expose_endpoint(self):
        url = os.environ["INPUT_API_URL"]
        response = requests.Response()
        response.status_code = 403
        response.url = url
        response._content = f'{{"error": "{url} test-secret"}}'.encode()
        failures = [
            (None, "HTTP 403"),
            (requests.exceptions.ConnectionError(f"Cannot connect to {url}"), "ConnectionError"),
            (requests.exceptions.Timeout(f"Timed out at {url}"), "Timeout"),
            (requests.exceptions.InvalidURL(f"Invalid URL: {url}"), "InvalidURL"),
        ]
        for failure, expected_error in failures:
            with self.subTest(error=expected_error):
                stdout = io.StringIO()
                with mock.patch("pr2changelog.api_caller.requests.post",
                                return_value=response, side_effect=failure), redirect_stdout(stdout):
                    try:
                        main.main()
                    except ApiError:
                        error_traceback = traceback.format_exc()
                    else:
                        self.fail("Expected the API request to fail")
                logged = stdout.getvalue() + error_traceback
                self.assertIn(expected_error, logged)
                self.assertNotIn(url, logged)
                self.assertNotIn("private-api.example", logged)
                self.assertNotIn("register-change", logged)
                self.assertNotIn("test-secret", logged)
