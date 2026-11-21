#!/usr/bin/env python3
"""Flag AI prose tells and banned punctuation in text that people will read.

Run on PR bodies, commit messages, Slack posts, review replies and docs before publishing.
Rules come from agents.md and pstack's unslop. Exit 1 lists each hit with the fix.
"""
import argparse
from pathlib import Path
import re
import sys

WORDS = ['additionally', 'crucial', 'delve', 'enhance', 'foster', 'landscape', 'pivotal', 'showcase', 'testament',
         'underscore', 'vibrant', 'leverage', 'utilize', 'seamless', 'robust solution', 'game-changer']
PUNCTUATION = [
    (re.compile('\u2014'), 'em dash: use a period, a comma or a plain hyphen'),
    (re.compile('\u2013'), 'en dash: use a hyphen or the word "to"'),
    (re.compile(r'^\s*>(?!\s*\[!)'), 'blockquote: quote with a fenced code block'),
]
# Phrase rules skip `code` and "quoted" spans, so a rule that names a banned phrase does not trip itself.
PHRASES = [
    (re.compile(r'co-authored-by:|generated with (claude|codex|cursor)|\U0001F916', re.I), 'AI attribution: remove it'),
    (re.compile(r'\b(' + '|'.join(map(re.escape, WORDS)) + r')\b', re.I), 'AI vocabulary: use the plain word'),
    (re.compile(r"\b(I hope this helps|let me know if|great question|you're absolutely right|it is important to note)\b", re.I), 'chatbot phrase: delete it'),
    (re.compile(r'\bnot just\b[^.\n]{1,80}\bbut\b', re.I), '"not just X but Y": state the point'),
]


QUOTED = re.compile(r'`[^`]*`|"[^"\n]*"')


def lint(text):
    fenced, hits = False, []
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith('```'):
            fenced = not fenced
            continue
        if fenced:
            continue
        masked = QUOTED.sub(lambda m: ' ' * len(m.group(0)), line)
        for pattern, message, source in [(p, m, line) for p, m in PUNCTUATION] + [(p, m, masked) for p, m in PHRASES]:
            for match in pattern.finditer(source):
                hits.append((number, match.start() + 1, match.group(0).strip(), message))
    return hits


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('files', nargs='*', help='Files to check; reads stdin when none are given')
    args = parser.parse_args()
    sources = [(name, Path(name).read_text()) for name in args.files] or [('<stdin>', sys.stdin.read())]
    failed = False
    for name, text in sources:
        for line, column, found, message in lint(text):
            failed = True
            print(f'{name}:{line}:{column}: {found!r} {message}')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
