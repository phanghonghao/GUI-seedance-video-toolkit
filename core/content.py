from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .utils import truncate


TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".json"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

SECTION_RULES = {
    "background": ["background", "problem", "pain", "challenge", "context", "market", "risk", "背景", "问题", "痛点", "现状"],
    "solution": ["solution", "product", "proposal", "overview", "system", "platform", "方案", "产品", "系统", "平台"],
    "features": ["feature", "function", "capability", "module", "workflow", "功能", "能力", "模块", "流程"],
    "technology": ["technology", "technical", "architecture", "implementation", "stack", "算法", "技术", "架构", "实现"],
    "results": ["result", "impact", "benefit", "advantage", "成果", "效果", "收益", "价值"],
    "plan": ["plan", "roadmap", "future", "timeline", "milestone", "next", "计划", "路线图", "展望", "下一步"],
}


@dataclass(slots=True)
class SourceScan:
    root: Path
    text_files: list[Path]
    image_files: list[Path]
    title_hint: str
    sections: dict[str, list[str]]


def scan_source_directory(source_dir: Path) -> SourceScan:
    text_files: list[Path] = []
    image_files: list[Path] = []
    title_hint = source_dir.name
    sections = {key: [] for key in SECTION_RULES}
    fallback_lines: list[str] = []

    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in TEXT_EXTENSIONS:
            text_files.append(path)
            content = _read_textual_content(path)
            if not content:
                continue
            extracted_title = _extract_title_hint(content)
            if extracted_title and title_hint == source_dir.name:
                title_hint = extracted_title
            blocks = _extract_blocks(content)
            fallback_lines.extend(
                snippet
                for _, snippet in blocks[:6]
                if not _is_low_signal_snippet(snippet)
            )
            for heading, snippet in blocks:
                if _is_low_signal_snippet(snippet):
                    continue
                matched = False
                lowered = f"{heading} {snippet}".strip().lower()
                for section, keywords in SECTION_RULES.items():
                    if any(keyword in lowered for keyword in keywords):
                        sections[section].append(snippet)
                        matched = True
                if not matched and len(sections["solution"]) < 4:
                    sections["solution"].append(snippet)
        elif suffix in IMAGE_EXTENSIONS:
            image_files.append(path)

    for key, values in sections.items():
        if not values:
            sections[key] = fallback_lines[:4]
        else:
            sections[key] = _unique_preserve(values)[:6]

    return SourceScan(
        root=source_dir,
        text_files=text_files,
        image_files=image_files,
        title_hint=title_hint,
        sections=sections,
    )


def _read_textual_content(path: Path) -> str:
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return json.dumps(payload, ensure_ascii=False, indent=2)
        except Exception:
            return path.read_text(encoding="utf-8", errors="ignore")
    return path.read_text(encoding="utf-8", errors="ignore")


def _extract_title_hint(content: str) -> str:
    for line in content.splitlines():
        candidate = line.strip().lstrip("#").strip()
        if candidate:
            return truncate(candidate, limit=80)
    return ""


def _extract_blocks(content: str) -> list[tuple[str, str]]:
    normalized = content.replace("\r\n", "\n")
    blocks = re.split(r"\n\s*\n", normalized)
    snippets: list[tuple[str, str]] = []
    pending_heading = ""
    for block in blocks:
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        heading = ""
        if lines and re.match(r"^\s*#{1,6}\s+", lines[0]):
            heading = _strip_markdown_prefix(lines[0])
        if heading and len(lines) == 1:
            pending_heading = heading
            continue
        if pending_heading and not heading:
            heading = pending_heading
            pending_heading = ""
        elif heading:
            pending_heading = ""
        compact = " ".join(_strip_markdown_prefix(line) for line in lines)
        compact = " ".join(compact.split())
        if len(compact) < 20:
            continue
        snippets.append((heading, truncate(compact, limit=220)))
    return snippets[:40]


def _unique_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def _strip_markdown_prefix(line: str) -> str:
    cleaned = line.strip()
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"^[-*+]\s+", "", cleaned)
    cleaned = re.sub(r"^\d+\.\s+", "", cleaned)
    return cleaned


def _is_low_signal_snippet(snippet: str) -> bool:
    lowered = snippet.lower()
    return "put markdown, text, json, and image files here" in lowered
