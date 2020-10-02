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
    pull_request:
        branches:
            - master
        types: [closed]

jobs:
    generate:
        if: github.event.pull_request.merged == true

        name: changelog generator
        runs-on: ubuntu-latest
        steps:
            
            - name: Checkout repository
              uses: actions/checkout@v2
              with:
                  fetch-depth: 0
                  
            - name: Generate changelog
              uses: corp-0/pr2changelog@master
              with:
                  repo: ${{ github.repository }}
                  pr_number: ${{ github.event.pull_request.number }}
                  
            -   name: Commit files
                run: |
                    git config --local user.email "action@github.com"
                    git config --local user.name "GitHub Action"
                    git commit -m "Add changes" -a
            -   name: Push changes
                uses: ad-m/github-push-action@master
                with:
                    github_token: ${{ secrets.GITHUB_TOKEN }}

```

Now add the changelog short description to your PRS like this
``CL: A short description of a change worthy of being mentioned in the changelog``

Every line in the PR body that starts with ``CL:`` will be considered to be a change mentioned in the changelog.