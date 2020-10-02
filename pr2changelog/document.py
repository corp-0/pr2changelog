import os
from .markdown import Markdown


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
                self.append_to_file(rec)

    def append_to_file(self, text):
        with open(self.file_name, 'a', encoding='UTF-8') as f:
            f.write(text)

    def clear_file(self):
        with open(self.file_name, 'w'):
            pass
