"""Exercise real packet files and input boundaries without a browser or network."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import review_packet as cli


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        self.context = self.root / "code.py"
        self.context.write_text('print("검토할 코드")\n# ```\n', encoding="utf-8")
        self.out = Path(self.temp.name) / "packet"

    def prepare(self, **kwargs):
        args = dict(root=self.root, question="수집 중간 응답을 최종으로 오인하는가?",
                    contexts=[self.context], reviewer="flash", out=self.out)
        args.update(kwargs)
        return cli.packet(**args)

    def test_packet_contains_actual_sources_and_matches_saved_hash(self):
        before = self.context.read_bytes()
        receipt = self.prepare()
        brief = (self.out / "entry.md").read_bytes().decode("utf-8")
        details = (self.out / "details.md").read_bytes().decode("utf-8")
        prompt = (self.out / "prompt.txt").read_bytes()
        meta = json.loads((self.out / "packet.json").read_text(encoding="utf-8"))
        self.assertIn("수집 중간 응답", brief)
        self.assertIn(before.decode(), details)
        self.assertIn("````\n", details)
        self.assertEqual(prompt, (brief + "\n" + details).encode())
        self.assertEqual(meta["prompt_sha256"], hashlib.sha256(prompt).hexdigest())
        self.assertEqual(meta["sources"][0]["sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(receipt["submission_attempts"], 0)
        self.assertEqual(self.context.read_bytes(), before)

    def test_duplicate_input_is_not_sent_twice_and_order_is_stable(self):
        result = self.prepare(contexts=[self.context, self.context])
        self.assertEqual(result["files"], 1)
        self.assertEqual(result["service"], "aistudio")

    def test_budget_rejection_does_not_create_partial_packet(self):
        with self.assertRaisesRegex(ValueError, "Nothing was truncated"):
            self.prepare(max_chars=5)
        self.assertFalse(self.out.exists())

    def test_existing_packet_is_never_overwritten(self):
        self.prepare()
        before = (self.out / "prompt.txt").read_bytes()
        with self.assertRaises(FileExistsError):
            self.prepare(question="다른 질문")
        self.assertEqual((self.out / "prompt.txt").read_bytes(), before)

    def test_outside_root_and_sensitive_paths_are_rejected_before_output(self):
        outside = self.root.parent / "outside.txt"
        outside.write_text("not selected project", encoding="utf-8")
        secret = self.root / ".env"
        secret.write_text("never read into a packet", encoding="utf-8")
        for path in (outside, secret):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.prepare(contexts=[path])
            self.assertFalse(self.out.exists())

    def test_empty_question_and_non_text_input_are_rejected(self):
        for text in ("", "  "):
            with self.assertRaises(ValueError):
                self.prepare(question=text)
        self.context.write_bytes(b"\xff\x00")
        with self.assertRaises(UnicodeError):
            self.prepare()
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
