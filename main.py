from pr2changelog.context import Context
from pr2changelog.document import Document
from pr2changelog.pr import PR


def main():
    c = Context()
    pr = PR(c.author, c.pr_number, c.url, c.change_token, c.body, categories=c.categories)
    pr.parse_body()
    Document(c.filename, pr.str_changes)


if __name__ == "__main__":
    main()
