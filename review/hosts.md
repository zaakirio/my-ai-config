# Code hosts: GitHub and Bitbucket

Reach a host by whatever the environment has, in this order: a native connector you are already signed into, an MCP server, then the CLI/REST calls below. The calls are the reference implementation and the only path CI has.
If a host is unreachable, do the parts you can and state plainly what you could not do. Never fake it.

Report PR links to a human as full canonical URLs, never a bare `#N`. A bare `#N` auto-links against the current repo, which is the wrong repo, and cannot express a Bitbucket PR at all.
- `https://github.com/<owner>/<repo>/pull/<N>`
- `https://bitbucket.org/<workspace>/<repo>/pull-requests/<N>`

## Detect and parse

```bash
REMOTE_URL=$(git remote get-url origin 2>/dev/null)
# contains github.com    -> github
# contains bitbucket.org -> bitbucket
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's#.*(github\.com|bitbucket\.org)[:/]##; s#\.git$##')
OWNER=${OWNER_REPO%%/*}; REPO=${OWNER_REPO##*/}
```

With `--repo <value>`: `owner/repo` with no host defaults to Bitbucket unless `--github` is passed; a full URL or a value containing a host resolves itself. Set OWNER/REPO from the override and never re-read the remote afterwards.

## Auth

GitHub: `gh` handles it (`gh auth login` or `GITHUB_TOKEN`).

Bitbucket: Basic auth, email plus Atlassian API token. Never Bearer, which fails with a 401 identical to a bad token.
```bash
BB_EMAIL=$(git config user.email)   # $BITBUCKET_TOKEN in env
curl -fsS -u "$BB_EMAIL:$BITBUCKET_TOKEN" "https://api.bitbucket.org/2.0/..."
```
Use `-f` so an auth redirect to an HTML login page fails loudly instead of parsing as empty JSON.

## Operations

| Operation | GitHub | Bitbucket (prefix `https://api.bitbucket.org/2.0/repositories/$OWNER/$REPO`) |
|---|---|---|
| PR details | `gh pr view N --json title,body,headRefName,headRefOid,baseRefName,url,author,additions,deletions,changedFiles` | `GET /pullrequests/N` |
| Diff | `gh pr diff N > "$DIFF"` | `GET /pullrequests/N/diff -o "$DIFF"` |
| Open PRs | `gh pr list --state open --limit 100 --json number,title,headRefName` | `GET /pullrequests?state=OPEN&pagelen=50` |
| Commits | `gh api repos/$OWNER/$REPO/pulls/N/commits --paginate` | `GET /pullrequests/N/commits?pagelen=100` |
| Inline + issue comments | `gh api repos/$OWNER/$REPO/pulls/N/comments --paginate` and `.../issues/N/comments --paginate` | `GET /pullrequests/N/comments?pagelen=100&sort=-created_on` |
| Reviews | `gh api repos/$OWNER/$REPO/pulls/N/reviews --paginate` | same comments endpoint; Bitbucket has no separate review object |
| Reply to a comment | `gh api repos/$OWNER/$REPO/pulls/N/comments/$ID/replies -X POST -f body=...` | `POST /pullrequests/N/comments` with `{"content":{"raw":...},"parent":{"id":$ID}}` |
| Plain comment | `gh pr comment N --body ...` | `POST /pullrequests/N/comments` with `{"content":{"raw":...}}` |
| Approve | review with `event=APPROVE` (see post-review.py) | `POST /pullrequests/N/approve` |
| Checks | `gh pr checks N` | `GET /commit/$SHA/statuses` |

Bitbucket comment fields: author `.user.display_name`, body `.content.raw`, file `.inline.path`, line `.inline.to`, created `.created_on`, deleted `.deleted`, resolved `.resolution != null`, parent `.parent.id`.
GitHub equivalents: `.user.login`, `.body`, `.path`, `.line` or `.original_line`, `.created_at`, `.in_reply_to_id`.

## Posting a review

Use `post-review.py` in this directory. It resolves every finding's anchor against the on-disk diff and posts inline comments plus the summary in one pass, for either host.

```bash
python3 ~/.claude/review/post-review.py --host github --owner "$OWNER" --repo "$REPO" \
  --pr "$PR" --findings "$DIR/findings.json" --diff "$DIR/diff.patch" --event COMMENT --head "$HEAD_SHA"
```

`findings.json`: `{"summary": "markdown", "findings": [{"file": "src/a.ts", "line": 42, "body": "...", "severity": "critical"}]}`.
A finding whose line does not appear on the new-file side of the diff is posted as a general comment with `file:line` in its text, never as an inline comment without an anchor (which silently lands at the top of the file).
Two gates live in the script rather than in prose, because both fail silently when a long run forgets them: it re-reads the PR head and exits non-zero if it moved or cannot be read, and it refuses `--event APPROVE` while any finding is critical, important, or still carrying `(unverified)`. Neither has an override.

Anchors must be new-file line numbers: the `@@ -a,b +c,d @@` header gives the hunk's starting new-file line, added and context lines advance the counter, removed lines do not. Removed lines cannot take comments.

## Head freshness

Resolve the head SHA from the PR object plus a forced ref fetch, never from a cached summary field, which serves stale SHAs (verification.md V6).

```bash
git fetch -q --force origin "refs/pull/$PR/head:refs/remotes/origin/pr/$PR" || echo "no head ref"
```
Bitbucket does not expose PR heads at a `refs/pull/N/head` equivalent; fetch the source branch by name instead.

## Gotchas

- Build any multiline JSON body with `python3 -c 'import json; ...'`. Bash heredocs break on markdown escaping; Bitbucket returns 400.
- Pipe captured JSON with `printf '%s'`, never `echo`. zsh expands backslash escapes in echo and turns a `\n` inside a JSON string into a real newline, which dies as "Invalid control character".
- Bitbucket PUT on a PR preserves fields absent from the body, so omit `title` to update only the description.
- A 401 means the credential is wrong; a 404 means the wrong workspace or repo slug. Do not collapse them into "unreachable".
