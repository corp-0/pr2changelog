from pr2changelog.api_caller import ApiCaller
from pr2changelog.comments import CommentError, PRCommenter
from pr2changelog.context import Context
from pr2changelog.document import Document
from pr2changelog.exceptions import InvalidCategory, MissingCategory, MissingContextInformation
from pr2changelog.gha_utils import gha_debug, gha_error, gha_warning, gha_print, gha_set_output
from pr2changelog.pr import PR


def main() -> None:
    gha_debug("Starting pr2changelog")
    context = Context()

    try:
        comment = process_pr(context)
    except (MissingCategory, InvalidCategory):
        update_pr_comment(context, (
            "Some changelog lines have missing or invalid categories.\n"
            f"Use `{context.change_token}: [Category] description` with one of the configured categories, "
            "or `[NOCL]` if no changelog is needed."
        ))
        raise
    except Exception:
        update_pr_comment(context, "Changelog generation failed. Check the workflow run for details.")
        raise

    update_pr_comment(context, comment)


def process_pr(context: Context) -> str | None:
    pr = PR(context.author, context.pr_number, context.url, context.change_token, context.body, context.categories)
    pr.parse_body()
    found_changes = check_found_changes(pr)

    if pr.skip_changelog:
        return None
    if not found_changes:
        return (
            "Your PR has no registered changes in its description.\n"
            f"Add `{context.change_token}: [Category] description` lines, or `[NOCL]` if no changelog is needed."
        )

    generated = generate_changelog(pr, context)
    if context.merged and not generated:
        return "Your PR was merged, but no changelog was generated. Check the action's file and API settings."
    return None


def generate_changelog(pr: PR, context: Context) -> bool:
    generated = False
    if context.write_to_file:
        write_changelog_file(pr, context)
        generated = True
    else:
        gha_print("Skipping writing changelog file because write_to_file is false!")

    if context.api_url and context.api_secret_token:
        make_api_call(pr, context)
        generated = True
    else:
        gha_print("Skipping api call because api_url and/or api_secret_token are missing!")
    return generated


def update_pr_comment(context: Context, message: str | None) -> None:
    if not context.comment_on_pr:
        return
    if message is not None and context.run_url:
        message += f"\n\n[Workflow run]({context.run_url})"
    try:
        commenter = PRCommenter(context.github_api_url, context.repository, context.pr_number, context.github_token)
        commenter.sync(message)
    except (CommentError, MissingContextInformation) as error:
        gha_warning(f"Unable to update PR comment: {error}")


def check_found_changes(pr: PR) -> bool:
    gha_debug("Checking if changes were found")
    gha_set_output("skip_changelog", int(pr.skip_changelog))

    if pr.skip_changelog:
        if not pr.body.strip():
            gha_print("PR body is empty: skipping changelog generation")
        else:
            gha_print("[NOCL] found: skipping changelog generation")
        gha_set_output("found_changes", 0)
        gha_set_output("generated_changelog", 0)
        gha_set_output("changelog_content", "")
        return False

    if not pr.changes:
        gha_warning("No changes found in PR body")
        gha_warning("Skipping whole process")
        gha_set_output("found_changes", 0)
        gha_set_output("generated_changelog", 0)
        return False
    else:
        gha_print("Changes found in PR body")
        gha_set_output("found_changes", 1)
        return True


def write_changelog_file(pr: PR, context: Context):
    gha_debug("Writing changelog file")

    doc = Document(context.filename, pr.str_changes)
    gha_set_output("generated_changelog", 1)
    gha_set_output("changelog_content", doc.raw_text)



def make_api_call(pr: PR, context: Context):
    gha_debug("Making api call")

    caller = ApiCaller(context.api_url, context.api_secret_token, pr)
    try:
        caller.post_changes()
    except Exception as e:
        gha_error(f"Error while making api call: {e}")
        raise e

    gha_set_output("generated_changelog", 1)
    gha_set_output("changelog_content", pr.str_changes)

if __name__ == "__main__":
    main()
