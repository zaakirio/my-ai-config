# Tickets: Jira and Linear

Interchangeable everywhere. Nothing downstream may branch on which one answered; it consumes the normalised fields at the bottom and names the provider once so a reader can check it.
Reach order is the same as hosts.md: native connector, MCP server, then the calls here.
No provider reachable means review the code on its own merits and say ticket context was unavailable. It never means the ticket had no acceptance criteria.

| | Jira | Linear |
|---|---|---|
| Auth env | `JIRA_API_TOKEN`, `JIRA_EMAIL`, `JIRA_INSTANCE` | `LINEAR_API_KEY` |
| Transport | REST v3, basic auth `email:token` | GraphQL, one endpoint |
| Auth header | `-u "$JIRA_EMAIL:$JIRA_API_TOKEN"` | `Authorization: $LINEAR_API_KEY`, no `Bearer` |
| Endpoint | `https://$JIRA_INSTANCE/rest/api/3/issue/$KEY` | `https://api.linear.app/graphql` |
| Body format | ADF (nested JSON) | markdown |
| Canonical URL | `https://$JIRA_INSTANCE/browse/$KEY` | the issue's own `url` |

A personal Linear key is sent raw; only OAuth tokens take `Bearer`. A wrong prefix and an invalid key both return the same `AUTHENTICATION_ERROR` 401, so the error text will not tell you which mistake you made. Check the header shape first.

## 1. Extract candidates

Both providers use `<PREFIX>-<NUMBER>`, so extraction yields candidates, never conclusions.

Pass 1, first match wins: a `linear.app/<ws>/issue/<KEY>/...` URL in title or body (confirms Linear outright), a `https://<host>/browse/<KEY>` URL (confirms Jira outright), then uppercase `[A-Z][A-Z0-9]+-[0-9]+` in title, then body, then branch.
The prefix class is `[A-Z][A-Z0-9]+`, not `[A-Z]{2,}`: keys may contain digits (`B2B-77`).

Pass 2, only if pass 1 found nothing. Linear's "copy git branch name" produces a lowercase branch (`feature/hitx-105-...`, `zaakir/eng-123-...`; the prefix is a workspace setting) that pass 1 cannot see.

```bash
TICKET_CANDIDATE=$(git branch --show-current \
  | grep -oiE '(^|[/_-])[a-z][a-z0-9]+-[0-9]+([^a-z0-9]|$)' \
  | grep -oiE '[a-z][a-z0-9]+-[0-9]+' | head -1 | tr '[:lower:]' '[:upper:]')
```

The trailing boundary is what rejects `feat/add-2fa`. It still yields `V1-2` from `release/v1-2-3` and `UTF-8` from `chore/utf-8-cleanup`, which is why step 2 must confirm every candidate before it reaches a review summary.

Matching a key against PRs is case-insensitive in both directions: uppercase for display, compare in lowercase. A case-sensitive search for `HITX-105` against a lowercase Linear branch finds nothing and reports "no open PR".

## 2. Resolve the candidate to a provider

Stop at the first answer:
1. `TICKET_PROVIDER` is `jira`, `linear` or `none`. Obey it; `none` skips ticket context.
2. The prefix appears in `LINEAR_TEAM_KEYS` or `JIRA_PROJECT_KEYS` (comma separated, optional).
3. Exactly one of `LINEAR_API_KEY` / `JIRA_API_TOKEN` or one connector is present. That one owns it. Common case, costs nothing.
4. Both configured: probe Linear, fall through to Jira.

```bash
export TICKET_CANDIDATE LINEAR_API_KEY
BODY=$(python3 -c 'import json,os; print(json.dumps({"query":"query($k:String!){issue(id:$k){identifier}}","variables":{"k":os.environ["TICKET_CANDIDATE"]}}))')
PROBE=$(curl -sS -X POST https://api.linear.app/graphql -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" --data "$BODY")
```

Classify on `errors[0].extensions.code`, never on HTTP status. Verified live:

| State | Response | Action |
|---|---|---|
| found | 200, `data.issue.identifier` set | Linear owns it |
| not ours | 200, code `INPUT_ERROR`, "Entity not found: Issue" | fall through to Jira |
| unreachable | 401, code `AUTHENTICATION_ERROR`, or non-JSON, or 5xx | say unreachable |

A miss is HTTP 200 with an errors array, never `{"data":{"issue":null}}`, so status-based logic reads it as success. Collapsing unreachable into not-found is the failure to avoid: the ticket then reviews as though it had no acceptance criteria, and both a wrong `Bearer` prefix and an expired key land there. Same distinction for Jira: 404 is "not this project", 401 is "the token is wrong".
If neither provider claims the candidate, discard it and proceed with no ticket context. Discarding is the correct outcome for a `V1-2`.

## 3. Fetch

```bash
JIRA_EMAIL="${JIRA_EMAIL:-$(git config user.email)}"
curl -fsS -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  "https://$JIRA_INSTANCE/rest/api/3/issue/$TICKET_KEY?fields=summary,description,comment,status,priority,issuelinks"
```
`description` and each comment body are ADF, not strings. Flatten `text` nodes depth first before looking for acceptance criteria, or the criteria read as empty and the review reports full coverage of nothing. An ADF checklist item is a `taskItem` node with `state` `DONE` or `TODO`.

```bash
LINEAR_QUERY='query T($key:String!){issue(id:$key){identifier title description url priorityLabel
  state{name} assignee{name} team{key name} labels{nodes{name}}
  parent{identifier title url} children{nodes{identifier title state{name}}}
  comments(first:20){nodes{body createdAt user{name}}}}}'
export LINEAR_QUERY TICKET_KEY LINEAR_API_KEY
BODY=$(python3 -c 'import json,os; print(json.dumps({"query":os.environ["LINEAR_QUERY"],"variables":{"key":os.environ["TICKET_KEY"]}}))')
curl -fsS -X POST https://api.linear.app/graphql -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" --data "$BODY"
```
`issue(id:)` takes the human identifier and is case-insensitive, so a lowercase branch candidate probes as-is. Build the payload with `json.dumps`; a hand-built JSON body breaks on the query's newlines.
Pipe the response with `printf '%s'`, never `echo` (hosts.md gotchas). Verified: a 5,125-character description over 46 newlines failed under `echo` and parsed under `printf`. This is the normal path, not an edge case.
If the response carries an `errors` array naming a field, GraphQL rejected the whole query over that one field and the issue looks missing when it is not. Drop the named field and retry once. Load-bearing fields are `identifier`, `title`, `description`, `url`, `state{name}`; everything else is enrichment.

## 4. Normalise

| Field | Jira | Linear |
|---|---|---|
| `TICKET_PROVIDER` | jira | linear |
| `TICKET_KEY` | `key` | `identifier` |
| `TICKET_URL` | `$JIRA_INSTANCE/browse/$KEY` | `url` |
| `TICKET_SUMMARY` | `fields.summary` | `title` |
| `TICKET_STATUS` | `fields.status.name` | `state.name` |
| `TICKET_PRIORITY` | `fields.priority.name` | `priorityLabel` |
| `TICKET_BODY` | `fields.description`, ADF flattened | `description` |
| `TICKET_COMMENTS` | `fields.comment.comments`, last 10 | `comments.nodes` |
| `TICKET_RELATED` | `fields.issuelinks` | `parent` plus `children.nodes` |

Acceptance criteria sit in different places. Jira: prose or a checklist in the description, sometimes a comment. Linear: markdown checkboxes in the description and often sub-issues, so a thin-looking Linear description may still carry the full requirement set in `children`. Read both before calling a requirement absent.

User-facing strings say "Ticket", and name the provider once:
`**Ticket:** [ENG-123](url) - Fix token refresh (Linear, In Progress)`

## Linking without side effects

Linear acts on PR text. Closing words: close/closes/closed/closing, fix/fixes/fixed/fixing, resolve/resolves/resolved/resolving, complete/completes/completed/completing, implement/implements/implemented/implementing. Non-closing: ref/refs/references, part of, contributes to, toward/towards.
So `implements ENG-123` completes a Linear issue even though `implements` is not a GitHub closing keyword, and `Fixes ENG-123` fires both trackers where they overlap.
Write the reference bare, as a key or a full URL with no verb in front, unless completing on merge is the intent. Linear still links on the ID appearing in branch, title or body.
