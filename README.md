# PR2Changelog

Generate changelog using a short description added to your PRs' descriptions.

# Why

Maybe you don't want to generate changelog on releases or maybe you don't want to enforce a particular
commit format to your contributors. This action allows PRs to declare changes and generate a changelog file from
that.

# Usage

Add the workflow file

```yml
name: pr2changelog
on:
    pull_request_target:
        branches:
            - master
        types: [closed]

jobs:
    generate:
        if: github.event.pull_request.merged == true

        name: changelog generator
        runs-on: ubuntu-latest
        permissions:
            contents: write
        steps:

            - name: Checkout repository
              uses: actions/checkout@v7
              with:
                  fetch-depth: 0

            - name: pr2changelog
              id: pr2changelog
              uses: corp-0/pr2changelog@master

            -   name: Commit files
                if: ${{ steps.pr2changelog.outputs.generated_changelog == 1}}
                run: |
                    git config --local user.email "action@github.com"
                    git config --local user.name "GitHub Action"
                    git add -- *
                    git commit -m "misc: update Changelog" -a
            -   name: Push changes
                if: ${{ steps.pr2changelog.outputs.generated_changelog == 1}}
                uses: ad-m/github-push-action@v1.3.0
                with:
                    github_token: ${{ secrets.GITHUB_TOKEN }}
```

Now add the changelog short description to your PRS like this
``CL: A short description of a change worthy of being mentioned in the changelog``

Every line in the PR body that starts with ``CL:`` will be considered to be a change mentioned in the changelog.

Add `[NOCL]` anywhere in the PR body to explicitly skip changelog generation.
The token is case-sensitive and takes precedence over all `CL:` lines, including
lines with missing or invalid categories. The action succeeds without requiring
changelog lines, writing a changelog file, or posting changes to the API.

A missing, null, empty, or whitespace-only PR body also skips changelog generation.
A nonempty body without `[NOCL]` still goes through normal parsing and validation.

When skipped, the outputs are `skip_changelog=1`, `found_changes=0`,
`generated_changelog=0`, and an empty `changelog_content`. Otherwise,
`skip_changelog=0` and normal changelog processing applies.

A downstream step can distinguish a skipped changelog from missing lines in a nonempty body:

```yml
- name: Require changelog lines unless explicitly skipped
  if: steps.pr2changelog.outputs.skip_changelog != '1' && steps.pr2changelog.outputs.found_changes != '1'
  run: |
    echo "::error::Add CL: lines or [NOCL] to the PR body."
    exit 1
```

Inputs:


| INPUT   |      DESC      |  DEFAULT |
|----------|-------------|------|
| change_token |  The string we will find in your PR body to determine if the line describes a change | "CL:" |
| file_name |    Name of the changelog file, including extension   |   "CHANGELOG.md" |

The Docker action runs Python 3.14; consuming workflows do not need to install Python.
Outputs use GitHub's `GITHUB_OUTPUT` file, including multiline changelog content.

# Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (CI uses
0.12.17), then run:

```sh
uv sync --locked
uv run --locked python -m unittest discover -v
uv build
docker build -t pr2changelog .
```

uv installs Python 3.14 automatically if needed. Run `uv lock --upgrade` to
update dependencies and commit the resulting `uv.lock`.

When running `main.py` outside GitHub Actions, set `GITHUB_EVENT_PATH` to a PR
event JSON file and `GITHUB_OUTPUT` to a writable output file. Summary helpers
also require `GITHUB_STEP_SUMMARY`.
