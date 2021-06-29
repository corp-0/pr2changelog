from os import system

from pr2changelog.context import Context
from pr2changelog.document import Document
from pr2changelog.pr import PR


def main():
    c = Context()
    pr = PR(c.author, c.pr_number, c.url, c.change_token, c.body, categories=c.categories)
    pr.parse_body()

    if not pr.changes:
        print("PR has no changes worthy enough to mention in changelog, skipping :)")
        system('echo "::set-output name=generated_changelog::0"')
        return

    doc = Document(c.filename, pr.str_changes)
    system('echo "::set-output name=generated_changelog::1"')
    system(f'echo "::set-output name=changelog_content::{doc.raw_text}"')


if __name__ == "__main__":
    main()
