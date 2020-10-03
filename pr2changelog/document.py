import os
from .markdown import Markdown
import re


class Document:
    """Object that represents the changelog file and all related operations"""
    changelog_content: list
    file_name: str

    def __init__(self, filename):
        self.file_name = filename
        self.read_file_content()

    def read_file_content(self):
        if not os.path.isfile("CHANGELOG.md"):
            with open(self.file_name, 'w', encoding='UTF-8'):
                pass
            self.changelog_content = [str()]
        else:
            with open(self.file_name, 'r', encoding='UTF-8') as f:
                self.changelog_content = f.readlines()

    def add_title(self):
        self.append_to_file(Markdown.title("CHANGELOG\n---\n\n"))

    def add_record(self, new_record):
        self.read_file_content()
        previous_records = [i for i in self.changelog_content if i and i.startswith("*")]
        self.clear_file()
        self.add_title()

        self.append_to_file(new_record)

        if previous_records:
            for rec in previous_records:
                if "api.github" in rec:
                    rec = self.fix_wrong_url(rec)
                self.append_to_file(rec)

    def append_to_file(self, text):
        with open(self.file_name, 'a', encoding='UTF-8') as f:
            f.write(text)

    def clear_file(self):
        with open(self.file_name, 'w'):
            pass

    def fix_wrong_url(self, text):
        wrong_user_patt = r"(https:\/\/api.github.com\/users\/(.+))\)\s"
        wrong_pr_patt = r"(https:\/\/api.github.com\/repos\/(\w+\/\w+)\/pulls\/(\d+))"

        user_match = re.search(wrong_user_patt, text)
        pr_match = re.search(wrong_pr_patt, text)

        if user_match is not None:
            text = text.replace(user_match.groups()[0], f"https://github.com/{user_match.groups()[1]}")

        if pr_match is not None:
            text = text.replace(pr_match.groups()[0],
                                f"https://github.com/{pr_match.groups()[1]}/pull/{pr_match.groups()[2]}")

        return text
