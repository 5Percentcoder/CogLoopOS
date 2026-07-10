#!/usr/bin/env python3
"""Deterministic kernel for the Personal Learning OS."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable


ALLOWED_STATUSES = {"captured", "experiment-ready", "blocked", "complete"}
REQUIRED_METADATA = {"id", "type", "status", "created", "updated", "tags"}
REQUIRED_SECTIONS = (
    "触发问题",
    "当前理解",
    "可证伪假设",
    "实验契约",
    "证据",
    "工程判断",
    "关联",
    "未来复用触发器",
    "下一步",
)
COMPLETE_PLACEHOLDERS = ("待运行", "待填写", "[TODO]", "TBD")
BEGIN_MARKER = "<!-- BEGIN GENERATED: LEARNING LOOPS -->"
END_MARKER = "<!-- END GENERATED: LEARNING LOOPS -->"
HUMAN_DECISION_HEADING = "## 9. Human Decision"
ID_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
LOCAL_EVIDENCE_PATTERN = re.compile(
    r"`((?:experiments|evidence|data)/[^`\n]+)`"
)


@dataclass(frozen=True)
class Issue:
    path: Path
    rule: str
    message: str
    remediation: str

    def format(self, root: Path) -> str:
        try:
            display_path = self.path.relative_to(root)
        except ValueError:
            display_path = self.path
        return (
            f"{display_path}: [{self.rule}] {self.message} "
            f"Remediation: {self.remediation}"
        )


@dataclass(frozen=True)
class LoopRecord:
    path: Path
    metadata: dict[str, object]
    title: str
    sections: dict[str, str]
    body: str

    @property
    def loop_id(self) -> str:
        return str(self.metadata.get("id", ""))

    @property
    def status(self) -> str:
        return str(self.metadata.get("status", ""))

    @property
    def updated(self) -> date:
        return date.fromisoformat(str(self.metadata["updated"]))

    @property
    def tags(self) -> list[str]:
        value = self.metadata.get("tags", [])
        return [str(item) for item in value] if isinstance(value, list) else []

    @property
    def next_action(self) -> str:
        value = self.sections.get("下一步", "")
        lines = [
            re.sub(r"^[-*]\s*", "", line.strip())
            for line in value.splitlines()
            if line.strip()
        ]
        return " ".join(lines) if lines else "未记录下一步"


class FrontmatterError(ValueError):
    pass


def parse_scalar(value: str) -> object:
    value = value.strip()
    if not value:
        return ""
    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in {'"', "'"}
    ):
        return value[1:-1]
    if value == "true":
        return True
    if value == "false":
        return False
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        raise FrontmatterError("file must start with YAML frontmatter")

    closing = text.find("\n---\n", 4)
    if closing == -1:
        raise FrontmatterError("frontmatter closing delimiter is missing")

    raw = text[4:closing]
    body = text[closing + 5 :]
    metadata: dict[str, object] = {}
    current_list_key: str | None = None

    for line_number, raw_line in enumerate(raw.splitlines(), start=2):
        if not raw_line.strip():
            continue
        if raw_line.startswith("  - "):
            if current_list_key is None:
                raise FrontmatterError(
                    f"line {line_number}: list item has no parent key"
                )
            items = metadata.setdefault(current_list_key, [])
            if not isinstance(items, list):
                raise FrontmatterError(
                    f"line {line_number}: key {current_list_key} is not a list"
                )
            items.append(parse_scalar(raw_line[4:]))
            continue
        if raw_line.startswith((" ", "\t")):
            raise FrontmatterError(
                f"line {line_number}: nested mappings are not supported"
            )
        if ":" not in raw_line:
            raise FrontmatterError(
                f"line {line_number}: expected 'key: value'"
            )

        key, value = raw_line.split(":", 1)
        key = key.strip()
        if not key:
            raise FrontmatterError(f"line {line_number}: key is empty")
        if key in metadata:
            raise FrontmatterError(
                f"line {line_number}: duplicate key {key}"
            )
        if value.strip():
            metadata[key] = parse_scalar(value)
            current_list_key = None
        else:
            metadata[key] = []
            current_list_key = key

    return metadata, body


def normalize_section_name(heading: str) -> str:
    return re.sub(r"^\d+\.\s*", "", heading.strip())


def extract_sections(body: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", body, flags=re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = normalize_section_name(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[name] = body[start:end].strip()
    return sections


def extract_title(body: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", body, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def parse_loop(path: Path) -> LoopRecord:
    text = path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    return LoopRecord(
        path=path,
        metadata=metadata,
        title=extract_title(body),
        sections=extract_sections(body),
        body=body,
    )


def parse_iso_date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def validate_record_basic(record: LoopRecord) -> list[Issue]:
    issues: list[Issue] = []
    missing_metadata = sorted(REQUIRED_METADATA - set(record.metadata))
    if missing_metadata:
        issues.append(
            Issue(
                record.path,
                "metadata.required",
                f"missing fields: {', '.join(missing_metadata)}",
                "add every required frontmatter field",
            )
        )

    loop_id = record.loop_id
    if not ID_PATTERN.fullmatch(loop_id):
        issues.append(
            Issue(
                record.path,
                "metadata.id",
                f"invalid loop id '{loop_id}'",
                "use YYYY-MM-DD-lowercase-topic-slug",
            )
        )
    if record.path.stem != loop_id:
        issues.append(
            Issue(
                record.path,
                "metadata.filename",
                f"filename '{record.path.stem}' does not match id '{loop_id}'",
                "rename the file or correct the id",
            )
        )
    if record.metadata.get("type") != "learning-loop":
        issues.append(
            Issue(
                record.path,
                "metadata.type",
                f"expected type learning-loop, got {record.metadata.get('type')!r}",
                "set type: learning-loop",
            )
        )
    if record.status not in ALLOWED_STATUSES:
        issues.append(
            Issue(
                record.path,
                "metadata.status",
                f"unsupported status '{record.status}'",
                f"use one of {', '.join(sorted(ALLOWED_STATUSES))}",
            )
        )

    created = parse_iso_date(record.metadata.get("created"))
    updated = parse_iso_date(record.metadata.get("updated"))
    if created is None:
        issues.append(
            Issue(
                record.path,
                "metadata.created",
                f"invalid created date {record.metadata.get('created')!r}",
                "use YYYY-MM-DD",
            )
        )
    if updated is None:
        issues.append(
            Issue(
                record.path,
                "metadata.updated",
                f"invalid updated date {record.metadata.get('updated')!r}",
                "use YYYY-MM-DD",
            )
        )
    if created and updated and updated < created:
        issues.append(
            Issue(
                record.path,
                "metadata.date-order",
                "updated date is earlier than created date",
                "correct the dates",
            )
        )

    if not isinstance(record.metadata.get("tags"), list):
        issues.append(
            Issue(
                record.path,
                "metadata.tags",
                "tags must be a YAML list",
                "write tags as indented '- value' items",
            )
        )
    if not record.title:
        issues.append(
            Issue(
                record.path,
                "body.title",
                "missing H1 title",
                "add a '# Title' heading",
            )
        )

    missing_sections = [
        name for name in REQUIRED_SECTIONS if name not in record.sections
    ]
    if missing_sections:
        issues.append(
            Issue(
                record.path,
                "body.sections",
                f"missing sections: {', '.join(missing_sections)}",
                "restore the sections from vault/90_System/Templates/learning-loop.md",
            )
        )
    return issues


def validate_complete_record(record: LoopRecord, root: Path) -> list[Issue]:
    if record.status != "complete":
        return []

    issues: list[Issue] = []
    body = record.body
    section_requirements = {
        "触发问题": (),
        "可证伪假设": ("Hypothesis", "如果假设错误"),
        "实验契约": ("主要指标", "通过阈值"),
        "证据": ("Observation",),
        "工程判断": ("Decision", "适用范围", "风险与限制"),
        "未来复用触发器": (),
    }
    for section_name, required_terms in section_requirements.items():
        content = record.sections.get(section_name, "").strip()
        if not content:
            issues.append(
                Issue(
                    record.path,
                    "complete.section-content",
                    f"section '{section_name}' is empty",
                    "add the required completion evidence",
                )
            )
            continue
        missing_terms = [term for term in required_terms if term not in content]
        if missing_terms:
            issues.append(
                Issue(
                    record.path,
                    "complete.section-contract",
                    f"section '{section_name}' lacks: {', '.join(missing_terms)}",
                    "use the learning-loop template contract",
                )
            )

    placeholders = [item for item in COMPLETE_PLACEHOLDERS if item in body]
    if placeholders:
        issues.append(
            Issue(
                record.path,
                "complete.placeholder",
                f"completed loop contains placeholders: {', '.join(placeholders)}",
                "replace placeholders or use experiment-ready/blocked status",
            )
        )

    experiment_contract = record.sections.get("实验契约", "")
    evidence_section = record.sections.get("证据", "")
    has_command = "运行命令" in experiment_contract and bool(
        re.search(r"`[^`\n]+`|```", experiment_contract)
    )
    has_external_evidence = bool(
        re.search(r"https?://", evidence_section)
        or re.search(r"外部.+证据", evidence_section)
    )
    local_paths = LOCAL_EVIDENCE_PATTERN.findall(body)
    if not has_command and not has_external_evidence:
        issues.append(
            Issue(
                record.path,
                "complete.reproduction",
                "no runnable command or named external evidence path",
                "add a reproduction command or explicit external evidence",
            )
        )
    if not local_paths and not has_external_evidence:
        issues.append(
            Issue(
                record.path,
                "complete.evidence-path",
                "no local evidence path or external evidence URL",
                "link the raw result or external evidence",
            )
        )

    for relative in sorted(set(local_paths)):
        evidence_path = root / relative
        if not evidence_path.exists():
            issues.append(
                Issue(
                    record.path,
                    "evidence.missing",
                    f"referenced path does not exist: {relative}",
                    "create the artifact or correct the path",
                )
            )
            continue
        if evidence_path.suffix == ".json":
            try:
                json.loads(evidence_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                issues.append(
                    Issue(
                        evidence_path,
                        "evidence.json",
                        f"invalid JSON result: {exc}",
                        "write valid machine-readable JSON",
                    )
                )
    return issues


def load_loops(root: Path) -> tuple[list[LoopRecord], list[Issue]]:
    loop_dir = root / "vault" / "10_Loops"
    if not loop_dir.exists():
        return [], [
            Issue(
                loop_dir,
                "repository.loop-dir",
                "learning-loop directory does not exist",
                "create vault/10_Loops",
            )
        ]

    records: list[LoopRecord] = []
    issues: list[Issue] = []
    for path in sorted(loop_dir.glob("*.md")):
        try:
            records.append(parse_loop(path))
        except (OSError, FrontmatterError) as exc:
            issues.append(
                Issue(
                    path,
                    "parse.frontmatter",
                    str(exc),
                    "repair the frontmatter using vault/90_System/Templates/learning-loop.md",
                )
            )

    by_id: dict[str, list[LoopRecord]] = {}
    for record in records:
        by_id.setdefault(record.loop_id, []).append(record)
    for loop_id, matches in by_id.items():
        if loop_id and len(matches) > 1:
            paths = ", ".join(str(item.path.name) for item in matches)
            for record in matches:
                issues.append(
                    Issue(
                        record.path,
                        "metadata.duplicate-id",
                        f"id '{loop_id}' is also used by: {paths}",
                        "assign one unique loop id and matching filename",
                    )
                )
    return records, issues


def sort_records(records: Iterable[LoopRecord]) -> list[LoopRecord]:
    by_id = sorted(records, key=lambda item: item.loop_id)
    return sorted(by_id, key=lambda item: item.updated, reverse=True)


def format_index_entry(record: LoopRecord, include_next: bool) -> str:
    entry = f"- [[{record.path.stem}]] — {record.title} (`{record.status}`)"
    if include_next:
        entry += f" — 下一步：{record.next_action}"
    return entry


def render_generated_index(records: Iterable[LoopRecord]) -> str:
    all_records = list(records)
    active = sort_records(
        item
        for item in all_records
        if item.status in {"captured", "experiment-ready"}
    )
    blocked = sort_records(item for item in all_records if item.status == "blocked")
    complete = sort_records(item for item in all_records if item.status == "complete")

    def render_group(
        heading: str, group: list[LoopRecord], include_next: bool
    ) -> list[str]:
        lines = [f"## {heading}", ""]
        if group:
            lines.extend(
                format_index_entry(record, include_next) for record in group
            )
        else:
            lines.append("暂无。")
        return lines

    lines = [BEGIN_MARKER]
    for heading, group, include_next in (
        ("Active", active, True),
        ("Blocked", blocked, True),
        ("Complete", complete, False),
    ):
        lines.extend(render_group(heading, group, include_next))
        lines.append("")
    lines.append(END_MARKER)
    return "\n".join(lines)


def replace_generated_region(index_text: str, generated: str) -> str:
    begin = index_text.find(BEGIN_MARKER)
    end = index_text.find(END_MARKER)
    if begin == -1 or end == -1 or end < begin:
        raise ValueError(
            "index must contain valid generated-region markers"
        )
    end += len(END_MARKER)
    return index_text[:begin] + generated + index_text[end:]


def validate_index(root: Path, records: list[LoopRecord]) -> list[Issue]:
    index_path = root / "vault" / "00_Index" / "Learning Loops.md"
    if not index_path.exists():
        return [
            Issue(
                index_path,
                "index.missing",
                "central index does not exist",
                "create the index and run sync-index",
            )
        ]
    text = index_path.read_text(encoding="utf-8")
    if BEGIN_MARKER not in text or END_MARKER not in text:
        return [
            Issue(
                index_path,
                "index.markers",
                "generated-region markers are missing",
                "add the markers and run sync-index",
            )
        ]
    expected = render_generated_index(records)
    try:
        synchronized = replace_generated_region(text, expected)
    except ValueError as exc:
        return [
            Issue(
                index_path,
                "index.markers",
                str(exc),
                "repair the marker order",
            )
        ]
    if synchronized != text:
        return [
            Issue(
                index_path,
                "index.drift",
                "central index is out of sync with loop frontmatter",
                "run python3 scripts/os.py sync-index",
            )
        ]
    return []


def validate_repository(root: Path, check_index: bool = True) -> list[Issue]:
    root = root.resolve()
    records, issues = load_loops(root)
    for record in records:
        issues.extend(validate_record_basic(record))
        issues.extend(validate_complete_record(record, root))
    if check_index and not any(
        issue.rule in {"parse.frontmatter", "metadata.duplicate-id"}
        for issue in issues
    ):
        issues.extend(validate_index(root, records))
    return issues


def sync_index(root: Path) -> bool:
    root = root.resolve()
    records, issues = load_loops(root)
    for record in records:
        issues.extend(validate_record_basic(record))
    blocking = [
        issue
        for issue in issues
        if issue.rule
        in {
            "parse.frontmatter",
            "metadata.duplicate-id",
            "metadata.id",
            "metadata.status",
            "metadata.updated",
        }
    ]
    if blocking:
        raise ValueError(
            "\n".join(issue.format(root) for issue in blocking)
        )

    index_path = root / "vault" / "00_Index" / "Learning Loops.md"
    text = index_path.read_text(encoding="utf-8")
    generated = render_generated_index(records)
    updated = replace_generated_region(text, generated)
    if updated == text:
        return False
    index_path.write_text(updated, encoding="utf-8")
    return True


def title_tokens(title: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]{2,}", title.lower()))


def possible_duplicates(records: list[LoopRecord]) -> list[tuple[LoopRecord, LoopRecord]]:
    matches: list[tuple[LoopRecord, LoopRecord]] = []
    for index, left in enumerate(records):
        left_tokens = title_tokens(left.title)
        for right in records[index + 1 :]:
            right_tokens = title_tokens(right.title)
            union = left_tokens | right_tokens
            intersection = left_tokens & right_tokens
            if not union:
                continue
            similarity = len(intersection) / len(union)
            if left.title.strip().lower() == right.title.strip().lower() or (
                len(intersection) >= 2 and similarity >= 0.6
            ):
                matches.append((left, right))
    return matches


def format_review_list(
    records: list[LoopRecord], review_date: date, include_next: bool = True
) -> list[str]:
    if not records:
        return ["暂无。"]
    lines: list[str] = []
    for record in sort_records(records):
        age = (review_date - record.updated).days
        stale = f"，已停滞 {age} 天" if age > 7 else ""
        line = (
            f"- [[{record.path.stem}]] — {record.title} "
            f"（更新：{record.updated.isoformat()}{stale}）"
        )
        if include_next:
            line += f"；下一步：{record.next_action}"
        lines.append(line)
    return lines


def extract_human_section(text: str) -> str | None:
    position = text.find(HUMAN_DECISION_HEADING)
    return text[position:].rstrip() if position != -1 else None


def default_human_section(root: Path) -> str:
    template_path = (
        root / "vault" / "90_System" / "Templates" / "weekly-review.md"
    )
    if template_path.exists():
        section = extract_human_section(
            template_path.read_text(encoding="utf-8")
        )
        if section:
            return section
    return (
        f"{HUMAN_DECISION_HEADING}\n\n"
        "- [ ] 接受建议\n"
        "- [ ] 调整建议\n"
        "- [ ] 暂不处理\n\n"
        "备注："
    )


def generate_weekly_review(root: Path, review_date: date) -> Path:
    root = root.resolve()
    records, load_issues = load_loops(root)
    validation_issues = list(load_issues)
    for record in records:
        validation_issues.extend(validate_record_basic(record))
        validation_issues.extend(validate_complete_record(record, root))
    validation_issues.extend(validate_index(root, records))

    iso_year, iso_week, _ = review_date.isocalendar()
    week_id = f"{iso_year}-W{iso_week:02d}"
    period_start = review_date - timedelta(days=review_date.weekday())
    period_end = period_start + timedelta(days=6)
    report_path = root / "vault" / "20_Reviews" / f"{week_id}.md"
    existing_human = None
    if report_path.exists():
        existing_human = extract_human_section(
            report_path.read_text(encoding="utf-8")
        )
    human_section = existing_human or default_human_section(root)

    active = [
        record
        for record in records
        if record.status in {"captured", "experiment-ready"}
    ]
    blocked = [record for record in records if record.status == "blocked"]
    completed_this_week = [
        record
        for record in records
        if record.status == "complete"
        and period_start <= record.updated <= period_end
    ]
    counts = {
        status: sum(record.status == status for record in records)
        for status in ("captured", "experiment-ready", "blocked", "complete")
    }
    duplicate_pairs = possible_duplicates(records)

    priorities: list[str] = []
    for record in sort_records(blocked):
        priorities.append(f"解除 [[{record.path.stem}]]：{record.next_action}")
    for record in sort_records(active):
        priorities.append(f"推进 [[{record.path.stem}]]：{record.next_action}")
    if not priorities:
        priorities.append("从一个真实工程问题启动下一条 learning loop。")
    priorities = priorities[:3]

    anomaly_lines = (
        [f"- {issue.format(root)}" for issue in validation_issues]
        if validation_issues
        else ["暂无。"]
    )
    duplicate_lines = (
        [
            f"- [[{left.path.stem}]] ↔ [[{right.path.stem}]]"
            for left, right in duplicate_pairs
        ]
        if duplicate_pairs
        else ["暂无。"]
    )

    lines = [
        "---",
        f"id: {week_id}",
        "type: weekly-review",
        "status: draft",
        f"created: {review_date.isoformat()}",
        f"updated: {review_date.isoformat()}",
        f"period_start: {period_start.isoformat()}",
        f"period_end: {period_end.isoformat()}",
        "---",
        "",
        f"# Weekly Review — {week_id}",
        "",
        "## 1. System Health",
        "",
        (
            "PASS：仓库结构校验无异常。"
            if not validation_issues
            else f"FAIL：发现 {len(validation_issues)} 个结构异常。"
        ),
        "",
        "## 2. Status Overview",
        "",
        f"- captured: {counts['captured']}",
        f"- experiment-ready: {counts['experiment-ready']}",
        f"- blocked: {counts['blocked']}",
        f"- complete: {counts['complete']}",
        "",
        "## 3. Active Loops",
        "",
        *format_review_list(active, review_date),
        "",
        "## 4. Blocked Loops",
        "",
        *format_review_list(blocked, review_date),
        "",
        "## 5. Completed This Week",
        "",
        *format_review_list(completed_this_week, review_date, include_next=False),
        "",
        "## 6. Structural Anomalies",
        "",
        *anomaly_lines,
        "",
        "## 7. Possible Duplicates",
        "",
        *duplicate_lines,
        "",
        "## 8. Proposed Priorities",
        "",
        *[f"{index}. {value}" for index, value in enumerate(priorities, start=1)],
        "",
        human_section,
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def default_root() -> Path:
    return Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=default_root(),
        help="repository root (defaults to the parent of scripts/)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate repository contracts")
    subparsers.add_parser("sync-index", help="regenerate the derived loop index")
    review = subparsers.add_parser(
        "weekly-review", help="generate a weekly health review"
    )
    review.add_argument(
        "--date",
        type=date.fromisoformat,
        default=date.today(),
        help="review date in YYYY-MM-DD form",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if args.command == "validate":
        issues = validate_repository(root)
        if issues:
            print(
                "\n".join(issue.format(root) for issue in issues),
                file=sys.stderr,
            )
            return 1
        records, _ = load_loops(root)
        print(f"PASS: {len(records)} learning loops are structurally valid.")
        return 0
    if args.command == "sync-index":
        try:
            changed = sync_index(root)
        except (OSError, ValueError) as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        print("UPDATED: index synchronized." if changed else "PASS: index already synchronized.")
        return 0
    if args.command == "weekly-review":
        report_path = generate_weekly_review(root, args.date)
        print(f"WROTE: {report_path}")
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
