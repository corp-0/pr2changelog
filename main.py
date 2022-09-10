from os import system

from pr2changelog.context import Context
from pr2changelog.document import Document
from pr2changelog.api_caller import ApiCaller
from pr2changelog.pr import PR


def main():
    c = Context()
    pr = PR(c.author, c.pr_number, c.url, c.change_token, c.body, categories=c.categories)
    pr.parse_body()

    if not pr.changes:
        print("PR has no changes skipping :)")
        system('echo "::set-output name=generated_changelog::0"')
        return

    if c.write_to_file:
        doc = Document(c.filename, pr.str_changes)
        system('echo "::set-output name=generated_changelog::1"')
        system(f'echo "::set-output name=changelog_content::{doc.raw_text}"')
    else:
        for change in pr.str_changes:
            system(f'echo "{change}"')

    if c.api_secret_token and c.api_url:
        system('echo "We are registering the changes in the changelog api!"')
        caller = ApiCaller(c.api_url, c.api_secret_token, pr)
        caller.post_changes()
        system('echo "::set-output name=generated_changelog::1"')
        system(f'echo "::set-output name=changelog_content::{pr.str_changes}')


if __name__ == "__main__":
    main()
