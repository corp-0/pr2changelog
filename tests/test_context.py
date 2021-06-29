import os
import unittest
from unittest import mock

from pr2changelog.context import Context
from pr2changelog.exceptions import MissingContextInformation
from pr2changelog.pr import Author

categories = "Fix;New;Improvement"
body = """CL:[Fix] fixed shit.
CL: [Improvement] improved shit
unrelated shit
CL:[New] new shit"""


@mock.patch.dict(os.environ, {"GITHUB_EVENT_PATH": "data/merged.json"}, clear=True)
class ConfigurationTest(unittest.TestCase):

    def test_required_env(self):
        names_to_remove = {"GITHUB_EVENT_PATH"}
        modified_environ = {
            k: v for k, v in os.environ.items() if k not in names_to_remove
        }

        with mock.patch.dict(os.environ, modified_environ, clear=True):
            with self.assertRaises(MissingContextInformation):
                Context()

    def test_autor_creation(self):
        expected = Author(username="Username", url="https://api.github.com/users/Codertocat")
        actual = Context().author

        self.assertEqual(expected, actual)

    @mock.patch.dict(os.environ, {"INPUT_CATEGORIES": categories})
    def test_categories(self):
        self.assertEqual(categories.split(";"), Context().categories)

    def test_pr_number(self):
        self.assertEqual("2", Context().pr_number)

    def test_pr_url(self):
        self.assertEqual("https://api.github.com/repos/Username/Repo/pulls/2", Context().url)

    @mock.patch.dict(os.environ, {"INPUT_CHANGE_TOKEN": "XD"})
    def test_change_token(self):
        self.assertEqual("XD", Context().change_token)

    def test_missinng_change_token(self):
        self.assertEqual("CL", Context().change_token)

    def test_body(self):
        self.assertEqual(body, Context().body)


if __name__ == '__main__':
    unittest.main()
