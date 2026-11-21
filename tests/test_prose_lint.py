from pathlib import Path
import subprocess
import unittest

LINT = Path(__file__).resolve().parents[1] / 'scripts/workflow/prose-lint.py'


def run(text):
    return subprocess.run(['python3', str(LINT)], input=text, text=True, capture_output=True)


class ProseLintTest(unittest.TestCase):
    def test_flags_each_tell_with_its_fix(self):
        bad = '\n'.join([
            'The fix \u2014 finally \u2014 landed.',
            'Pages 1\u20133 changed.',
            '> quoted reviewer text',
            'Co-authored-by: Bot <bot@example.com>',
            'We leverage the cache to enhance speed.',
            'I hope this helps!',
            'This is not just faster, but safer.',
        ])
        result = run(bad)
        self.assertEqual(result.returncode, 1)
        for message in ['em dash', 'en dash', 'blockquote', 'AI attribution', 'AI vocabulary', 'chatbot phrase', 'not just X but Y']:
            self.assertIn(message, result.stdout)
        self.assertIn('<stdin>:1:9:', result.stdout)

    def test_clean_text_and_code_fences_pass(self):
        clean = 'Fixed the race in the poller.\nTests pass at abc1234.\n```\n> raw log \u2014 kept verbatim\n```\n- a list item with a-hyphen\n'
        result = run(clean)
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == '__main__':
    unittest.main()
