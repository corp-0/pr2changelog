import os
import unittest
from unittest import mock

from pr2changelog.document import Document
from pr2changelog.exceptions import ChangeLogFileNotFound


class DocumentTest(unittest.TestCase):
    data = {
        "filename": ".mockUpFile",
        "new_changes": [
            "* 10/10/10 [Fix] fixed a bug by [username](https://url.com/username) in PR #[1234]("
            "https://url.com/username/repo/pulls/1234)",
            "* 10/10/10 [New] added a thing by [username](https://url.com/username) in PR #[1234]("
            "https://url.com/username/repo/pulls/1234)",
        ],
        "create": True,
    }

    @classmethod
    def setUpClass(cls) -> None:
        with open("tests/data/test_CHANGELOG.md", "r", encoding="UTF-8") as f:
            cls.result = f.read()
        with open("tests/data/test_CHANGELOG_2.md", "r", encoding="UTF-8") as f:
            cls.result2 = f.read()

    def test_creates_when_missing_file(self):
        Document(**self.data)
        self.assertTrue(os.path.isfile(".mockUpFile"))

    def test_exception_when_missing_file(self):
        with mock.patch.dict(self.data, {"create": False}):
            self.assertRaises(ChangeLogFileNotFound, Document, **self.data)

    def test_doc_creation_when_no_previous_changes(self):
        doc = Document(**self.data)
        self.assertEqual(self.result, doc.raw_text)

    def test_doc_creation_when_previous_changes(self):
        with open(".mockUpFile", "w", encoding="UTF-8") as f:
            f.write(self.result)
        doc = Document(**self.data)
        self.assertEqual(self.result2, doc.raw_text)

    def test_skip_token_in_description(self):
        import sys
        from io import StringIO

        from pr2changelog.pr import PR

        test_pr = PR(
            **{
                "number": 1234,
                "title": "Test PR",
                "body": "__skipcl__",
                "user": {"login": "username", "html_url": "https://url.com/username"},
                "html_url": "https://url.com/username/repo/pulls/1234",
                "merge_commit_sha": "abcd1234",
                "head": {"ref": "branch-name"},
                "base": {"ref": "main"},
                "merged_at": "2022-01-01T00:00:00Z",
                "labels": [{"name": "skip-changelog"}],
            }
        )
        test_pr.parse_body()

        old_stdout = sys.stdout
        sys.stdout = new_stdout = StringIO()

        with self.assertRaises(ChangeLogFileNotFound) as cm:
            Document(pr=test_pr, **self.data)

        output = new_stdout.getvalue()
        sys.stdout = old_stdout

        self.assertEqual(str(cm.exception), "Changelog generation was skipped.")
        self.assertIn("Changelog generation was skipped.", output)

    def tearDown(self) -> None:
        if os.path.isfile(".mockUpFile"):
            os.remove(".mockUpFile")


if __name__ == "__main__":
    unittest.main()
