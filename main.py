from pr2changelog.api_caller import ApiCaller
from pr2changelog.context import Context
from pr2changelog.document import Document
from pr2changelog.gha_utils import gha_debug, gha_error, gha_warning, gha_print, gha_set_output
from pr2changelog.pr import PR


def main():
    gha_debug("Starting pr2changelog")

    context = Context()

    pr = PR(context.author, context.pr_number, context.url, context.change_token, context.body, context.categories)
    pr.parse_body()

    if not check_found_changes(pr):
        return

    if context.write_to_file:
        write_changelog_file(pr, context)
    else:
        gha_debug("Skipping writing changelog file because write_to_file is false!")

    if context.api_url and context.api_secret_token:
        make_api_call(pr, context)
    else:
        gha_debug("Skipping api call because api_url and/or api_secret_token are missing!")


def check_found_changes(pr: PR) -> bool:
    gha_debug("Checking if changes were found")

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
