import datetime
import unittest

from pr2changelog.markdown import Markdown
from pr2changelog.pr import Change, Author


class ChangeTest(unittest.TestCase):
    author = Author("username", "https://url.com/username")

    change_data = {
        "author": author,
        "desc": "fixed a bug",
        "category": "Fix",
        "pr_number": "1234",
        "pr_url": "https://url.com/username/repo/pulls/1234"
    }

    def test_style_with_category(self):
        date = datetime.datetime.today().strftime("%Y/%m/%d")
        c = Change(**self.change_data)
        expected_str = f"* {date}: **[{c.category}]** {c.desc} by " \
                       f"{Markdown.link(self.change_data.get('author').username, self.change_data.get('author').url)} " \
                       f"in PR #{Markdown.link(self.change_data.get('pr_number'), self.change_data.get('pr_url'))}"
        self.assertEqual(expected_str, c.styled())


if __name__ == '__main__':
    unittest.main()