import datetime
from .markdown import Markdown
import re


class Change:
    change_token: str
    author_name: str
    author_url: str
    pr_number: str
    pr_url: str
    change_lines: list

    def __init__(self, change_token:str, pr_data: dict):
        self.change_token = change_token
        self.author_name = pr_data['user']['login']
        self.author_url = pr_data['user']['url']
        self.pr_number = pr_data['number']
        self.pr_url = pr_data['url']
        self.change_lines = self.parse_changes(pr_data['body'])

    def format_change_line(self, line: str):
        date = datetime.datetime.today()
        date_str = f"{date.year}/{date.month}/{date.day}"

        return f"* {date_str}: {line} by {Markdown.link(self.author_name, self.author_url)} " \
               f"in PR #{Markdown.link(self.pr_number, self.pr_url)}\n"

    def parse_changes(self, pr_body: str):
        regex = f"^{self.change_token}.+$"
        matches = re.finditer(regex, pr_body, re.MULTILINE)
        changes = [(i.group()).replace("CL:", "").strip() for i in matches]

        return changes

    def get_changes(self):
        return [self.format_change_line(i) for i in self.change_lines]
