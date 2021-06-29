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
            "https://url.com/username/repo/pulls/1234)"],
        "create": True,
    }

    @classmethod
    def setUpClass(cls) -> None:
        with open("tests/data/test_CHANGELOG.md", 'r', encoding='UTF-8') as f:
            cls.result = f.read()
        with open("tests/data/test_CHANGELOG_2.md", 'r', encoding='UTF-8') as f:
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
        with open(".mockUpFile", 'w', encoding='UTF-8') as f:
            f.write(self.result)
        doc = Document(**self.data)
        self.assertEqual(self.result2, doc.raw_text)

    def tearDown(self) -> None:
        if os.path.isfile(".mockUpFile"):
            os.remove(".mockUpFile")


if __name__ == '__main__':
    unittest.main()
