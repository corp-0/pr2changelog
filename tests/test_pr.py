import unittest
from unittest import TestCase, mock

from pr2changelog.exceptions import (
    ChangeLogFileNotFound,
    InvalidCategory,
    MissingCategory,
)
from pr2changelog.pr import PR, Author


class PRTest(TestCase):
    author = Author("username", "https://url.com/username")
    test_data = {
        "author": author,
        "number": "1234",
        "url": "https://url.com/username/repo/pulls/1234",
        "change_token": "CL",
        "body": "CL: [Fix] fixed a bug",
    }
    body_multiple = "CL:[Fix] fixed a bug\nCL: improved a thing\nCL:[New] added a thing"
    categories = ["Fix", "Improve", "New"]

    def test_find_change_in_body(self):
        pr = PR(**self.test_data)
        pr.parse_body()
        self.assertEqual(1, len(pr.changes))

    def test_find_changes_in_body_3(self):
        with mock.patch.dict(self.test_data, {"body": self.body_multiple}):
            pr = PR(**self.test_data)
            pr.parse_body()
            self.assertEqual(3, len(pr.changes))

    def test_change_has_category(self):
        pr = PR(**self.test_data)
        pr.parse_body()
        self.assertTrue(pr.changes[0].category)

    def test_change_no_category_not_required(self):
        pr = PR(**self.test_data)
        try:
            pr.parse_body()
        except MissingCategory:
            self.fail("Category was not required. We shouldn't have raised exception.")

    def test_change_missing_required_category(self):
        with mock.patch.dict(
            self.test_data, {"body": "CL: fixed a bug", "categories": self.categories}
        ):
            pr = PR(**self.test_data)
            self.assertRaises(MissingCategory, pr.parse_body)

    def test_changes_1_missing_required_category(self):
        with mock.patch.dict(
            self.test_data, {"body": self.body_multiple, "categories": self.categories}
        ):
            pr = PR(**self.test_data)
            self.assertRaises(MissingCategory, pr.parse_body)

    def test_invalid_category(self):
        with mock.patch.dict(
            self.test_data,
            {"body": "CL: [Wrong] wrong category", "categories": self.categories},
        ):
            pr = PR(**self.test_data)
            self.assertRaises(InvalidCategory, pr.parse_body)

    def test_category_when_not_required(self):
        with mock.patch.dict(self.test_data, {"body": "CL: [Wrong] wrong category"}):
            pr = PR(**self.test_data)
            pr.parse_body()
            self.assertEqual(pr.changes[0].category, "Wrong")

    def test_skip_token_in_description(self):
        with mock.patch.dict(self.test_data, {"body": "__skipcl__"}):
            pr = PR(**self.test_data)
            pr.parse_body()
            self.assertTrue(pr.skipped)
            with self.assertRaises(ChangeLogFileNotFound) as cm:
                pr.create_changelog()
            self.assertEqual(str(cm.exception), "Changelog generation was skipped.")


if __name__ == "__main__":
    unittest.main()
