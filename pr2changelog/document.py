import os
from dataclasses import dataclass, field
from typing import List

from .exceptions import ChangeLogFileNotFound
from .markdown import Markdown


@dataclass
class Document:
    filename: str
    new_changes: List[str]
    create: bool = True
    raw_text: str = field(default="")
    old_changes: List[str] = field(default_factory=list)

    def __post_init__(self):
        try:
            if not os.path.isfile(self.filename):
                self.handle_missing_file()
            self.read_old_changes()
            self.compose_text()
            self.write_final_doc()
        except ChangeLogFileNotFound as e:
            if "skipped" in str(e):
                print("Changelog generation was skipped.")
                return

    def handle_missing_file(self):
        if not self.create:
            raise ChangeLogFileNotFound(self.filename)
        print(f"{self.filename} couldn't be found but we're creating it now!")
        f = open(self.filename, "w", encoding="UTF-8")
        f.close()

    def read_old_changes(self):
        with open(self.filename, "r", encoding="UTF-8") as f:
            self.old_changes = [
                c.strip("\n") for c in f.readlines() if c.startswith("*")
            ]

    def compose_text(self):
        self.raw_text = Markdown.title("CHANGELOG\n---\n\n")
        for n in self.new_changes:
            self.raw_text += n + "\n"
        for c in self.old_changes:
            self.raw_text += c + "\n"

        if self.raw_text[-1] == "\n":
            self.raw_text = self.raw_text[:-1]

    def write_final_doc(self):
        with open(self.filename, "w", encoding="UTF-8") as f:
            f.write(self.raw_text)
