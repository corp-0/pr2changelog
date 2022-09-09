import requests
from pr2changelog.pr import PR, Change
from pr2changelog.exceptions import MissingContextInformation, ApiError

class ApiCaller:
    def __init__(self, url: str, api_token:str, pr: PR):
        self.url = url
        self.api_token = api_token
        self.pr = pr
        self.validate()

    def validate(self):
        if not self.url:
            raise MissingContextInformation("api url")
        if not self.api_token:
            raise MissingContextInformation("api token")
        if not self.pr:
            raise MissingContextInformation("pr")

    def post_changes(self):
        for change in self.pr.changes:
            data = self.build_post_data(change)
            response = requests.post(self.url, data=data)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                raise ApiError(self.url, response.json())

    def build_post_data(self, change: Change) -> dict:
        data = {
            "author_username": change.author.username,
            "author_url": change.author.url,
            "pr_number": self.pr.number,
            "pr_url": self.pr.url,
            "category": change.category.upper(),
            "secret_token": self.api_token,
        }

        return data
