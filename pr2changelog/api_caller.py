import requests

from pr2changelog.exceptions import MissingContextInformation, ApiError
from pr2changelog.gha_utils import gha_debug, gha_error
from pr2changelog.pr import PR, Change


class ApiCaller:
    def __init__(self, url: str, api_token:str, pr: PR):
        self.url = url
        self.api_token = api_token
        self.pr = pr
        self.validate()

    def validate(self):
        gha_debug("Validating API Caller")

        if not self.url:
            raise MissingContextInformation("api url")
        if not self.api_token:
            raise MissingContextInformation("api token")
        if not self.pr:
            raise MissingContextInformation("pr")

    def post_changes(self):
        gha_debug("Posting changes to API")

        for change in self.pr.changes:
            gha_debug(f"Attempting to post change: {change}")

            data = self.build_post_data(change)
            response = requests.post(self.url, data=data)
            gha_debug(f"got response: {response}")
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                gha_error(f"Error posting change: {change}")
                raise ApiError(self.url, response.json())
            except Exception as e:
                gha_error(f"Error posting change: {change}")
                raise ApiError(self.url, f"Unknown error: {e}\n{response.json()}")

    def build_post_data(self, change: Change) -> dict:
        gha_debug("Building post data")

        data = {
            "author_username": change.author.username,
            "author_url": change.author.url,
            "pr_number": self.pr.number,
            "pr_url": self.pr.url,
            "category": change.category.upper(),
            "description": change.desc,
            "secret_token": self.api_token,
        }
        gha_debug(f"Post data: {data}")

        return data
