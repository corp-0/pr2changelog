from typing import TypedDict, cast

import requests

from pr2changelog.exceptions import MissingContextInformation


class CommentAuthor(TypedDict):
    type: str


class IssueComment(TypedDict):
    id: int
    body: str | None
    user: CommentAuthor | None


class CommentError(Exception):
    pass


class PRCommenter:
    marker = "<!-- pr2changelog -->"

    def __init__(self, api_url: str, repository: str, pr_number: str, token: str):
        if not token:
            raise MissingContextInformation("github_token for PR comments")
        if not repository:
            raise MissingContextInformation("GITHUB_REPOSITORY for PR comments")
        self.base_url = f"{api_url.rstrip('/')}/repos/{repository}"
        self.pr_number = pr_number
        self.token = token

    def _request(self, session: requests.Session, method: str, path: str,
                 body: str | None = None, params: dict[str, int] | None = None) -> requests.Response:
        try:
            response = session.request(
                method, f"{self.base_url}/{path}",
                json={"body": body} if body is not None else None,
                params=params, timeout=30, allow_redirects=False,
            )
        except requests.exceptions.RequestException as error:
            raise CommentError(type(error).__name__) from None
        if not 200 <= response.status_code < 300:
            raise CommentError(f"GitHub returned HTTP {response.status_code}")
        return response

    def _find_comments(self, session: requests.Session) -> list[IssueComment]:
        managed = []
        page = 1
        while True:
            response = self._request(session, "GET", f"issues/{self.pr_number}/comments",
                                     params={"per_page": 100, "page": page})
            try:
                comments = cast(list[IssueComment], response.json())
            except ValueError:
                raise CommentError("GitHub returned invalid JSON") from None
            for comment in comments:
                author = comment["user"]
                if (author and author["type"] == "Bot"
                        and self.marker in (comment["body"] or "").splitlines()):
                    managed.append(comment)
            if len(comments) < 100:
                return managed
            page += 1

    def sync(self, message: str | None) -> None:
        with requests.Session() as session:
            session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            })
            comments = self._find_comments(session)
            if message is not None:
                body = f"{self.marker}\n{message}"
                if comments:
                    current = comments.pop(0)
                    if current["body"] != body:
                        self._request(session, "PATCH", f"issues/comments/{current['id']}", body)
                else:
                    self._request(session, "POST", f"issues/{self.pr_number}/comments", body)
            for comment in comments:
                self._request(session, "DELETE", f"issues/comments/{comment['id']}")
