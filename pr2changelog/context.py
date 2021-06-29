import json
import os
from typing import List

from pr2changelog.exceptions import MissingContextInformation
from pr2changelog.pr import Author


def read_payload():
    file = os.getenv("GITHUB_EVENT_PATH")
    if file is None:
        raise MissingContextInformation("path to github payload file")

    with open(file, 'r', encoding='UTF-8') as f:
        return json.load(f)


def findCategories():
    categories = os.getenv("INPUT_CATEGORIES")
    if not categories:
        return None
    return categories.split(";")


def find_change_token():
    token = os.getenv("INPUT_CHANGE_TOKEN", "CL")
    return token


def find_filename():
    filename = os.getenv("INPUT_FILENAME", "CHANGELOG.md")
    return filename


class Context:
    def __init__(self):
        self.payload = read_payload()
        self.filename = find_filename()
        self.categories: List[str] = findCategories()
        self.change_token = find_change_token()
        self.pr_number = self.find_pr_number()
        self.url = self.find_url()
        self.body = self.find_body()
        read_payload()

        self.author = Author(username="Username", url="https://api.github.com/users/Codertocat")

    def find_pr(self):
        pr = self.payload.get("pull_request")
        if pr is None:
            raise MissingContextInformation("PR data from payload. Was this not triggered by a PR?")
        return pr

    def find_pr_number(self):
        pr_number = self.payload.get("number")
        if pr_number is None:
            raise MissingContextInformation("PR number")

        return str(pr_number)

    def find_url(self):
        url = self.find_pr().get("url")
        if url is None:
            raise MissingContextInformation("PR url")

        return url

    def find_body(self):
        body = self.find_pr().get("body")
        if body is None:
            raise MissingContextInformation("PR body")

        return body

