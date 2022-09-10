import datetime
import re
from dataclasses import dataclass, field
from typing import List

from .exceptions import MissingCategory, InvalidCategory
from .markdown import Markdown
from os import system


@dataclass
class Author:
    username: str
    url: str

    def __str__(self):
        return self.username


@dataclass
class Change:
    author: Author
    desc: str
    pr_number: str
    pr_url: str
    category: field(default="")

    def styled(self) -> str:
        date = datetime.datetime.today().strftime("%Y/%m/%d")

        return f"* {date}: **[{self.category}]** {self.desc.strip()} by " \
               f"{Markdown.link(self.author.username, self.author.url)} " \
               f"in PR #{Markdown.link(self.pr_number, self.pr_url)}"

    def __str__(self):
        return f"{'['+self.category+'] ' if self.category else None}{self.desc} by {self.author.username}"


@dataclass
class PR:
    author: Author
    number: str
    url: str
    change_token: str
    body: str
    categories: List[str] = field(default_factory=list)
    changes: List[Change] = field(default_factory=list)
    regex = r"^({}):\s?(\[\w+\])?(.*)$"

    def parse_body(self):
        matches = re.finditer(self.regex.format(self.change_token), self.body, re.MULTILINE)
        for m in matches:
            system(f'echo "Found change: {m.string}')
            cat = m.groups()[1]
            if cat:
                cat = cat.replace("[", "").replace("]", "")
            desc = m.groups()[2]

            if self.requires_category and not cat:
                raise MissingCategory(m.string)
            if self.requires_category and cat not in self.categories:
                raise InvalidCategory(cat, self.categories)

            c = Change(self.author, desc, self.number, self.url, cat)
            self.changes.append(c)

    @property
    def requires_category(self) -> bool:
        return bool(self.categories)

    @property
    def str_changes(self):
        return [c.styled() for c in self.changes]

    def __str__(self):
        return f"PR: #{self.number} by {self.author.username}"
