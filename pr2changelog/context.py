import json
import os
from typing import List

from pr2changelog.exceptions import MissingContextInformation
from pr2changelog.gha_utils import gha_error, gha_debug
from pr2changelog.pr import Author


def read_payload():
    gha_debug("Reading payload")
    file = os.getenv("GITHUB_EVENT_PATH")
    if file is None:
        gha_error("GITHUB_EVENT_PATH is not set")
        raise MissingContextInformation("path to github payload file")

    try:
        with open(file, 'r', encoding='UTF-8') as f:
            return json.load(f)
    except FileNotFoundError:
        gha_error("Payload file not found")
        raise MissingContextInformation("github payload file")
    except json.JSONDecodeError:
        gha_error("Payload file is not valid JSON")
        raise MissingContextInformation("github payload file")
    except Exception as e:
        gha_error(f"Failed to read payload file for unknown error: {e}")
        raise e


def findCategories():
    gha_debug("Reading categories from settings")
    categories = os.getenv("INPUT_CATEGORIES")
    if not categories:
        gha_error("No categories found in settings. They won't be enforced!")
        return None

    gha_debug(f"Found categories: {categories.split(';')}")
    return categories.split(";")


def find_change_token():
    gha_debug("Reading change token from settings")
    token = os.getenv("INPUT_CHANGE_TOKEN", "CL")
    gha_debug(f"Found change token: {token}")
    return token


def find_filename():
    gha_debug("Reading filename from settings")
    filename = os.getenv("INPUT_FILENAME", "CHANGELOG.md")
    gha_debug(f"Found filename: {filename}")
    return filename


def find_api_secret_token():
    gha_debug("Reading secret token from settings")
    token = os.getenv("INPUT_API_SECRET_TOKEN", "")
    gha_debug(f"Found secret token: Not gonna tell you which one tho")
    return token


def find_write_to_file():
    gha_debug("Reading write to file from settings")
    write = os.getenv("INPUT_WRITE_TO_FILE", "true")

    gha_debug(f"Found write to file: {write.lower() == 'true'}")
    return write.lower() == "true"


def find_api_url():
    gha_debug("Reading API URL from settings")
    url = os.getenv("INPUT_API_URL", "")
    gha_debug(f"Found API URL: {url}")
    return url


class Context:
    def __init__(self):
        gha_debug("Reading context")
        self.payload = read_payload()
        self.filename = find_filename()
        self.categories: List[str] = findCategories()
        self.change_token = find_change_token()
        self.pr_number = self.find_pr_number()
        self.url = self.find_url()
        self.body = self.find_body()
        self.api_url = find_api_url()
        self.api_secret_token = find_api_secret_token()
        self.write_to_file = find_write_to_file()
        read_payload()

        self.author = self.find_author()

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

    def find_author(self):
        author_name = self.find_pr().get("user").get("login")
        author_url = self.find_pr().get("user").get("html_url")

        return Author(author_name, author_url)

    def find_url(self):
        url = self.find_pr().get("html_url")
        if url is None:
            raise MissingContextInformation("PR url")

        return url

    def find_body(self):
        body = self.find_pr().get("body")
        if body is None:
            raise MissingContextInformation("PR body")

        return body
