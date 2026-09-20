import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import main
from pr2changelog.comments import CommentError
from pr2changelog.exceptions import ApiError, InvalidCategory


class CommentIntegrationTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.event = self.directory / "event.json"
        environment = mock.patch.dict(os.environ, {
            "GITHUB_EVENT_PATH": str(self.event),
            "GITHUB_OUTPUT": str(self.directory / "output"),
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_RUN_ID": "123",
            "INPUT_COMMENT_ON_PR": "true",
            "INPUT_GITHUB_TOKEN": "github-secret",
            "INPUT_CATEGORIES": "Fix;New",
            "INPUT_WRITE_TO_FILE": "false",
        }, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        commenter = mock.patch("main.PRCommenter")
        self.commenter_class = commenter.start()
        self.commenter = self.commenter_class.return_value
        self.addCleanup(commenter.stop)

    def write_event(self, body: str | None, merged: bool = False) -> None:
        payload = json.loads(Path("tests/data/merged.json").read_text())
        payload["pull_request"]["body"] = body
        payload["pull_request"]["merged"] = merged
        self.event.write_text(json.dumps(payload))

    def test_comments_are_opt_in(self):
        self.write_event("No changelog")
        with mock.patch.dict(os.environ, {"INPUT_COMMENT_ON_PR": "false"}):
            main.main()
        self.commenter_class.assert_not_called()

    @mock.patch.dict(os.environ, {"INPUT_CHANGE_TOKEN": "LOG"})
    def test_missing_changes_comment_uses_configured_token_and_run_link(self):
        self.write_event("No changelog")
        main.main()
        self.commenter_class.assert_called_once_with("https://api.github.com", "owner/repo", "2", "github-secret")
        message = self.commenter.sync.call_args.args[0]
        self.assertIn("no registered changes", message)
        self.assertIn("LOG: [Category] description", message)
        self.assertIn("https://github.com/owner/repo/actions/runs/123", message)

    def test_valid_dry_check_and_skipped_bodies_clear_warning(self):
        for body in ("CL: [Fix] fixed a bug", "[NOCL]", None, "", " \n"):
            with self.subTest(body=body):
                self.commenter.reset_mock()
                self.write_event(body)
                main.main()
                self.commenter.sync.assert_called_once_with(None)

    def test_invalid_category_comments_and_keeps_failure(self):
        self.write_event("CL: [Wrong] invalid")
        with self.assertRaises(InvalidCategory):
            main.main()
        self.assertIn("missing or invalid categories", self.commenter.sync.call_args.args[0])

    @mock.patch.dict(os.environ, {"INPUT_API_URL": "https://private-api.example", "INPUT_API_SECRET_TOKEN": "api-secret"})
    @mock.patch("main.make_api_call", side_effect=ApiError("HTTP 503"))
    def test_api_failure_comments_and_keeps_failure(self, api):
        self.write_event("CL: [Fix] fixed a bug", merged=True)
        with self.assertRaises(ApiError):
            main.main()
        message = self.commenter.sync.call_args.args[0]
        self.assertIn("Changelog generation failed", message)
        for secret in ("https://private-api.example", "api-secret", "github-secret"):
            self.assertNotIn(secret, message)

    def test_merged_without_destination_warns(self):
        self.write_event("CL: [Fix] fixed a bug", merged=True)
        main.main()
        self.assertIn("file and API settings", self.commenter.sync.call_args.args[0])

    @mock.patch.dict(os.environ, {"INPUT_API_URL": "https://private-api.example", "INPUT_API_SECRET_TOKEN": "api-secret"})
    @mock.patch("main.make_api_call")
    def test_successful_submission_clears_warning(self, api):
        self.write_event("CL: [Fix] fixed a bug", merged=True)
        main.main()
        api.assert_called_once()
        self.commenter.sync.assert_called_once_with(None)

    def test_comment_failure_is_nonfatal(self):
        self.write_event("CL: [Fix] fixed a bug")
        self.commenter.sync.side_effect = CommentError("GitHub returned HTTP 403")
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            main.main()
        self.assertIn("::warning::Unable to update PR comment: GitHub returned HTTP 403", stdout.getvalue())

    @mock.patch.dict(os.environ, {"INPUT_API_URL": "https://private-api.example", "INPUT_API_SECRET_TOKEN": "api-secret"})
    @mock.patch("main.make_api_call", side_effect=ApiError("HTTP 503"))
    def test_comment_failure_does_not_replace_api_failure(self, api):
        self.write_event("CL: [Fix] fixed a bug", merged=True)
        self.commenter.sync.side_effect = CommentError("GitHub returned HTTP 403")
        with self.assertRaisesRegex(ApiError, "HTTP 503"):
            main.main()
