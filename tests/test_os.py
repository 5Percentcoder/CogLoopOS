from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts import os as learning_os


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"


class LearningOSTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        (self.root / "vault" / "10_Loops").mkdir(parents=True)
        (self.root / "vault" / "00_Index").mkdir(parents=True)
        (self.root / "vault" / "90_System" / "Templates").mkdir(parents=True)
        (self.root / "vault" / "00_Index" / "Learning Loops.md").write_text(
            "# Learning Loops\n\n"
            "Human introduction.\n\n"
            f"{learning_os.BEGIN_MARKER}\n"
            f"{learning_os.END_MARKER}\n",
            encoding="utf-8",
        )
        shutil.copy(
            REPO_ROOT
            / "vault"
            / "90_System"
            / "Templates"
            / "weekly-review.md",
            self.root
            / "vault"
            / "90_System"
            / "Templates"
            / "weekly-review.md",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def copy_fixture(self, name: str, preserve_name: bool = False) -> Path:
        source = FIXTURES / name
        if preserve_name:
            destination = self.root / "vault" / "10_Loops" / name
        else:
            metadata, _ = learning_os.parse_frontmatter(
                source.read_text(encoding="utf-8")
            )
            destination = (
                self.root
                / "vault"
                / "10_Loops"
                / f"{metadata['id']}.md"
            )
        shutil.copy(source, destination)
        return destination

    def add_complete_evidence(self, passed: bool = False) -> None:
        experiment = (
            self.root
            / "experiments"
            / "2026-07-04-complete-topic"
        )
        experiment.mkdir(parents=True)
        (experiment / "evaluate.py").write_text(
            "print('fixture')\n", encoding="utf-8"
        )
        (experiment / "result.json").write_text(
            json.dumps({"passed": passed}) + "\n",
            encoding="utf-8",
        )

    def sync(self) -> None:
        learning_os.sync_index(self.root)


class ParsingAndValidationTests(LearningOSTestCase):
    def test_parse_frontmatter_supports_required_list_subset(self) -> None:
        metadata, body = learning_os.parse_frontmatter(
            (FIXTURES / "captured.md").read_text(encoding="utf-8")
        )
        self.assertEqual(metadata["status"], "captured")
        self.assertEqual(metadata["tags"], ["learning-loop"])
        self.assertIn("# Captured Topic", body)

    def test_all_valid_status_fixtures_pass_basic_validation(self) -> None:
        for name in (
            "captured.md",
            "experiment-ready.md",
            "blocked.md",
            "complete.md",
        ):
            path = self.copy_fixture(name)
            record = learning_os.parse_loop(path)
            self.assertEqual(
                learning_os.validate_record_basic(record),
                [],
                msg=name,
            )

    def test_complete_loop_accepts_negative_experiment_result(self) -> None:
        path = self.copy_fixture("complete.md")
        self.add_complete_evidence(passed=False)
        record = learning_os.parse_loop(path)
        self.assertEqual(
            learning_os.validate_complete_record(record, self.root),
            [],
        )

    def test_invalid_fixture_reports_actionable_contract_errors(self) -> None:
        path = self.copy_fixture("invalid.md", preserve_name=True)
        record = learning_os.parse_loop(path)
        rules = {
            issue.rule
            for issue in learning_os.validate_record_basic(record)
        }
        self.assertTrue(
            {
                "metadata.id",
                "metadata.filename",
                "metadata.type",
                "metadata.status",
                "metadata.created",
                "body.sections",
            }.issubset(rules)
        )

    def test_duplicate_ids_are_reported_for_both_files(self) -> None:
        self.copy_fixture("duplicate-a.md", preserve_name=True)
        self.copy_fixture("duplicate-b.md", preserve_name=True)
        _, issues = learning_os.load_loops(self.root)
        duplicates = [
            issue for issue in issues if issue.rule == "metadata.duplicate-id"
        ]
        self.assertEqual(len(duplicates), 2)

    def test_complete_loop_rejects_placeholder_and_missing_evidence(self) -> None:
        path = self.copy_fixture("complete.md")
        text = path.read_text(encoding="utf-8").replace(
            "B 降低 12%", "待运行"
        )
        path.write_text(text, encoding="utf-8")
        record = learning_os.parse_loop(path)
        rules = {
            issue.rule
            for issue in learning_os.validate_complete_record(
                record, self.root
            )
        }
        self.assertIn("complete.placeholder", rules)
        self.assertIn("evidence.missing", rules)


class IndexTests(LearningOSTestCase):
    def test_sync_index_groups_records_and_is_idempotent(self) -> None:
        for name in (
            "captured.md",
            "experiment-ready.md",
            "blocked.md",
            "complete.md",
        ):
            self.copy_fixture(name)
        self.add_complete_evidence()

        self.assertTrue(learning_os.sync_index(self.root))
        first = (
            self.root / "vault" / "00_Index" / "Learning Loops.md"
        ).read_text(encoding="utf-8")
        self.assertFalse(learning_os.sync_index(self.root))
        second = (
            self.root / "vault" / "00_Index" / "Learning Loops.md"
        ).read_text(encoding="utf-8")

        self.assertEqual(first, second)
        self.assertIn("## Active", first)
        self.assertIn("## Blocked", first)
        self.assertIn("## Complete", first)
        self.assertIn("下一步：运行最小实验。", first)
        self.assertIn("Human introduction.", first)

    def test_sync_index_rejects_missing_markers(self) -> None:
        self.copy_fixture("captured.md")
        index = self.root / "vault" / "00_Index" / "Learning Loops.md"
        index.write_text("# No markers\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "generated-region markers"):
            learning_os.sync_index(self.root)

    def test_validate_detects_index_drift(self) -> None:
        self.copy_fixture("captured.md")
        issues = learning_os.validate_repository(self.root)
        self.assertIn("index.drift", {issue.rule for issue in issues})
        self.sync()
        self.assertEqual(learning_os.validate_repository(self.root), [])


class WeeklyReviewTests(LearningOSTestCase):
    def test_weekly_review_uses_iso_week_boundaries_and_stale_signal(self) -> None:
        loop_path = self.copy_fixture("captured.md")
        loop_path.write_text(
            loop_path.read_text(encoding="utf-8")
            .replace("created: 2026-07-01", "created: 2025-12-01")
            .replace("updated: 2026-07-01", "updated: 2025-12-01"),
            encoding="utf-8",
        )
        self.sync()
        report = learning_os.generate_weekly_review(
            self.root, date(2026, 1, 1)
        )
        text = report.read_text(encoding="utf-8")
        self.assertEqual(report.name, "2026-W01.md")
        self.assertIn("period_start: 2025-12-29", text)
        self.assertIn("period_end: 2026-01-04", text)
        self.assertIn("已停滞", text)

    def test_weekly_review_handles_empty_repository(self) -> None:
        self.sync()
        report = learning_os.generate_weekly_review(
            self.root, date(2026, 7, 9)
        )
        text = report.read_text(encoding="utf-8")
        self.assertIn("captured: 0", text)
        self.assertIn("complete: 0", text)
        self.assertIn("PASS：仓库结构校验无异常。", text)

    def test_weekly_review_preserves_human_decision(self) -> None:
        self.copy_fixture("captured.md")
        self.sync()
        report = learning_os.generate_weekly_review(
            self.root, date(2026, 7, 9)
        )
        original = report.read_text(encoding="utf-8")
        custom = original.replace("备注：", "备注：保留我的人工判断。")
        report.write_text(custom, encoding="utf-8")

        learning_os.generate_weekly_review(self.root, date(2026, 7, 9))
        regenerated = report.read_text(encoding="utf-8")
        self.assertIn("备注：保留我的人工判断。", regenerated)

    def test_possible_duplicate_titles_are_suggested(self) -> None:
        first = self.copy_fixture("captured.md")
        second = self.copy_fixture("experiment-ready.md")
        first.write_text(
            first.read_text(encoding="utf-8").replace(
                "# Captured Topic", "# RAG Query Evaluation"
            ),
            encoding="utf-8",
        )
        second.write_text(
            second.read_text(encoding="utf-8").replace(
                "# Experiment Ready Topic",
                "# RAG Query Evaluation Baseline",
            ),
            encoding="utf-8",
        )
        self.sync()
        report = learning_os.generate_weekly_review(
            self.root, date(2026, 7, 9)
        )
        text = report.read_text(encoding="utf-8")
        self.assertIn(
            "[[2026-07-01-captured-topic]] ↔ "
            "[[2026-07-02-ready-topic]]",
            text,
        )


if __name__ == "__main__":
    unittest.main()
