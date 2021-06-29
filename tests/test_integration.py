import os
import unittest
from unittest import mock

import main


# TODO improve these tests, I'm too lazy now!
@mock.patch.dict(os.environ, {"GITHUB_EVENT_PATH": "tests/data/merged.json", "INPUT_FILENAME": ".MockUpFile"},
                 clear=True)
class IntegrationTest(unittest.TestCase):
    def test_default_options(self):
        try:
            main.main()
        except Exception:
            self.fail()

    @mock.patch.dict(os.environ, {"INPUT_CATEGORIES": "Fix;New;Improvement"})
    def test_with_categories(self):
        try:
            main.main()
        except Exception:
            self.fail()

    def tearDown(self) -> None:
        if os.path.isfile(".mockUpFile"):
            os.remove(".mockUpFile")


if __name__ == '__main__':
    unittest.main()
