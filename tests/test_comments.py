import json
import traceback
import unittest
from unittest import mock

import requests

from pr2changelog.comments import CommentError, PRCommenter
from pr2changelog.exceptions import MissingContextInformation


def response(status: int = 200, comments: list[dict[str, object]] | None = None) -> requests.Response:
    result = requests.Response()
    result.status_code = status
    result._content = json.dumps(comments if comments is not None else []).encode()
    return result


def comment(identifier: int, body: str, author_type: str = "Bot") -> dict[str, object]:
    return {"id": identifier, "body": body, "user": {"type": author_type}}


class CommentTest(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch("pr2changelog.comments.requests.Session")
        self.session = patcher.start().return_value.__enter__.return_value
        self.session.headers = {}
        self.addCleanup(patcher.stop)
        self.commenter = PRCommenter("https://api.github.com", "owner/repo", "42", "github-secret")

    def test_creates_warning_with_authentication_and_timeout(self):
        self.session.request.side_effect = [response(), response(201)]
        self.commenter.sync("Missing changelog")
        self.assertEqual("Bearer github-secret", self.session.headers["Authorization"])
        self.assertEqual("2026-03-10", self.session.headers["X-GitHub-Api-Version"])
        self.session.request.assert_called_with(
            "POST", "https://api.github.com/repos/owner/repo/issues/42/comments",
            json={"body": "<!-- pr2changelog -->\nMissing changelog"},
            params=None, timeout=30, allow_redirects=False,
        )

    def test_updates_existing_warning_and_removes_duplicates(self):
        comments = [comment(1, "<!-- pr2changelog -->\nOld"),
                    comment(2, "<!-- pr2changelog -->\nDuplicate")]
        self.session.request.side_effect = [response(comments=comments), response(), response(204)]
        self.commenter.sync("New")
        calls = self.session.request.call_args_list
        self.assertEqual(("PATCH", "https://api.github.com/repos/owner/repo/issues/comments/1"), calls[1].args)
        self.assertEqual({"body": "<!-- pr2changelog -->\nNew"}, calls[1].kwargs["json"])
        self.assertEqual(("DELETE", "https://api.github.com/repos/owner/repo/issues/comments/2"), calls[2].args)

    def test_unchanged_warning_is_not_reposted(self):
        self.session.request.return_value = response(comments=[comment(1, "<!-- pr2changelog -->\nSame")])
        self.commenter.sync("Same")
        self.assertEqual(1, self.session.request.call_count)

    def test_removes_only_managed_bot_comments(self):
        comments = [comment(1, "<!-- pr2changelog -->\nOld"),
                    comment(2, "<!-- pr2changelog -->\nHuman comment", "User"),
                    comment(3, "Unrelated bot comment"),
                    comment(4, "Mentioning <!-- pr2changelog --> inline"),
                    {"id": 5, "body": None, "user": None}]
        self.session.request.side_effect = [response(comments=comments), response(204)]
        self.commenter.sync(None)
        self.assertEqual(2, self.session.request.call_count)
        self.assertEqual(("DELETE", "https://api.github.com/repos/owner/repo/issues/comments/1"),
                         self.session.request.call_args.args)

    def test_no_warning_to_remove_is_a_noop(self):
        self.session.request.return_value = response()
        self.commenter.sync(None)
        self.assertEqual(1, self.session.request.call_count)

    def test_finds_warning_on_later_page(self):
        first_page = [comment(index, "Other comment") for index in range(100)]
        self.session.request.side_effect = [response(comments=first_page),
                                           response(comments=[comment(101, "<!-- pr2changelog -->\nOld")]),
                                           response()]
        self.commenter.sync("New")
        calls = self.session.request.call_args_list
        self.assertEqual({"page": 1, "per_page": 100}, calls[0].kwargs["params"])
        self.assertEqual({"page": 2, "per_page": 100}, calls[1].kwargs["params"])
        self.assertEqual(("PATCH", "https://api.github.com/repos/owner/repo/issues/comments/101"), calls[2].args)

    def test_enterprise_api_url(self):
        self.session.request.return_value = response()
        PRCommenter("https://github.example/api/v3/", "owner/repo", "42", "token").sync(None)
        self.assertEqual("https://github.example/api/v3/repos/owner/repo/issues/42/comments",
                         self.session.request.call_args.args[1])

    def test_http_failure_does_not_expose_response_body(self):
        failed = response(403)
        failed._content = b'github-secret https://private-api.example'
        self.session.request.return_value = failed
        with self.assertRaisesRegex(CommentError, "^GitHub returned HTTP 403$"):
            self.commenter.sync("Warning")

    def test_network_failure_does_not_expose_exception_details(self):
        self.session.request.side_effect = requests.exceptions.Timeout("github-secret https://private-api.example")
        try:
            self.commenter.sync("Warning")
        except CommentError:
            output = traceback.format_exc()
        else:
            self.fail("Expected CommentError")
        self.assertIn("Timeout", output)
        self.assertNotIn("github-secret", output)
        self.assertNotIn("https://private-api.example", output)

    def test_invalid_json_is_reported_safely(self):
        invalid = response()
        invalid._content = b'not JSON github-secret'
        self.session.request.return_value = invalid
        with self.assertRaisesRegex(CommentError, "^GitHub returned invalid JSON$"):
            self.commenter.sync(None)

    def test_redirect_is_not_followed(self):
        self.session.request.return_value = response(302)
        with self.assertRaisesRegex(CommentError, "HTTP 302"):
            self.commenter.sync("Warning")
        self.assertFalse(self.session.request.call_args.kwargs["allow_redirects"])

    def test_requires_token_and_repository(self):
        for repository, token in (("owner/repo", ""), ("", "token")):
            with self.subTest(repository=repository), self.assertRaises(MissingContextInformation):
                PRCommenter("https://api.github.com", repository, "42", token)
        self.session.request.assert_not_called()
