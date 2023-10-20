import datetime
import re
from dataclasses import dataclass, field
from typing import List

from pr2changelog.gha_utils import gha_debug, gha_error
from .exceptions import MissingCategory, InvalidCategory
from .markdown import Markdown


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
    regex = r"^({}):\s?(\[\w+\])?(.+)$"

    def parse_body(self):
        gha_debug(f"Parsing PR body for {self}")
        gha_debug(self.body)

        matches = re.finditer(self.regex.format(self.change_token), self.body, re.MULTILINE)
        if not matches:
            gha_debug(f"Regex expression: {self.regex.format(self.change_token)} found no matches!")

        for m in matches:
            cat = m.groups()[1]
            if cat:
                gha_debug(f"Found category: {cat}")
                cat = cat.replace("[", "").replace("]", "")
            desc = m.groups()[2]

            if self.requires_category and not cat:
                gha_error(f"Missing category for change: {desc}")
                raise MissingCategory(m.string)
            if self.requires_category and cat not in self.categories:
                gha_error(f"Invalid category: {cat} for change: {desc}")
                raise InvalidCategory(cat, self.categories)

            change = Change(self.author, desc, self.number, self.url, cat)
            gha_debug(f"Built change object from PR body: {change}")
            self.changes.append(change)

    @property
    def requires_category(self) -> bool:
        return bool(self.categories)

    @property
    def str_changes(self):
        return [c.styled() for c in self.changes]

    def __str__(self):
        return f"PR: #{self.number} by {self.author.username}"
