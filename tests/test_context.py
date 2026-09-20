import os
import unittest
from unittest import mock

import pr2changelog.context
from pr2changelog.context import Context
from pr2changelog.exceptions import MissingContextInformation
from pr2changelog.pr import Author

categories = "Fix;New;Improvement"
body = """CL:[Fix] fixed shit.
CL: [Improvement] improved shit
unrelated shit
CL:[New] new shit"""


@mock.patch.dict(os.environ, {"GITHUB_EVENT_PATH": "tests/data/merged.json"}, clear=True)
class ContextTest(unittest.TestCase):

    def test_required_env(self):
        names_to_remove = {"GITHUB_EVENT_PATH"}
        modified_environ = {
            k: v for k, v in os.environ.items() if k not in names_to_remove
        }

        with mock.patch.dict(os.environ, modified_environ, clear=True):
            with self.assertRaises(MissingContextInformation):
                Context()

    def test_autor_creation(self):
        expected = Author(username="Username", url="https://url.com/Username")
        actual = Context().author
        self.assertEqual(expected, actual)

        with mock.patch.object(
                pr2changelog.context,
                'read_payload',
                return_value={
                    "number": 3,
                    "pull_request": {
                        "body": "ñe",
                        "html_url": "https://url.com/username2/pulls/3",
                        "user": {
                            "login": "Username2",
                            "html_url": "https://url.com/username",
                        }
                    }
                }):
            expected2 = Author(username="Username2", url="https://url.com/username")
            actual2 = Context().author
            self.assertEqual(expected2, actual2)

    @mock.patch.dict(os.environ, {"INPUT_CATEGORIES": categories})
    def test_categories(self):
        self.assertEqual(categories.split(";"), Context().categories)

    def test_pr_number(self):
        self.assertEqual("2", Context().pr_number)

    def test_pr_url(self):
        self.assertEqual("https://github.com/Codertocat/Hello-World/pull/2", Context().url)

    @mock.patch.dict(os.environ, {"INPUT_CHANGE_TOKEN": "XD"})
    def test_change_token(self):
        self.assertEqual("XD", Context().change_token)

    def test_missinng_change_token(self):
        self.assertEqual("CL", Context().change_token)

    def test_body(self):
        self.assertEqual(body, Context().body)

    def test_absent_body_becomes_empty_string(self):
        for body_fields in ({}, {"body": None}, {"body": ""}):
            with self.subTest(body_fields=body_fields):
                payload = pr2changelog.context.read_payload()
                payload["pull_request"].pop("body", None)
                payload["pull_request"].update(body_fields)
                with mock.patch.object(pr2changelog.context, "read_payload", return_value=payload):
                    self.assertEqual("", Context().body)

    def test_missing_pull_request_still_fails(self):
        with mock.patch.object(pr2changelog.context, "read_payload", return_value={"number": 2}):
            with self.assertRaises(MissingContextInformation):
                Context()

    @mock.patch.dict(os.environ, {"INPUT_FILE_NAME": "custom.md", "INPUT_FILENAME": "legacy.md"})
    def test_file_name_input(self):
        self.assertEqual("custom.md", Context().filename)

    @mock.patch.dict(os.environ, {"INPUT_FILENAME": "legacy.md"})
    def test_legacy_filename_input(self):
        self.assertEqual("legacy.md", Context().filename)


if __name__ == '__main__':
    unittest.main()
