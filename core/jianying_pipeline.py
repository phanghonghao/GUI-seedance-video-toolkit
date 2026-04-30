from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .app_context import AppContext
from .config_loader import env_or_value
from .job import JobContext
from .utils import ensure_directory, read_json


PLAYABLE_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
STATIC_MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def run_jianying_pipeline(app: AppContext, job: JobContext, dry_run: bool = False) -> dict:
    jianying_dir = ensure_directory(Path(job.data["outputs"]["jianying_dir"]))
    media_manifest_path = Path(job.data["outputs"]["media_dir"]) / "media_manifest.json"
    if not media_manifest_path.exists():
        raise FileNotFoundError("Run the video command before the jianying command.")

    media_manifest = read_json(media_manifest_path)
    config = _load_jianying_config(app)

    asset_items = []
    timeline_items = []
    for item in media_manifest["items"]:
        output_path = Path(item["output_file"])
        has_ready_media = output_path.exists() and output_path.suffix.lower() in (
            PLAYABLE_VIDEO_EXTENSIONS | STATIC_MEDIA_EXTENSIONS
        )
        status = "ready" if has_ready_media else "pending"
        asset_items.append(
            {
                "id": item["id"],
                "title": item["title"],
                "mode": item["mode"],
                "status": status,
                "path": str(output_path.resolve()),
            }
        )
        timeline_items.append(
            {
                "scene_id": item["id"],
                "title": item["title"],
                "media_path": str(output_path.resolve()),
                "status": status,
                "voice": config["voice"],
                "transition": config["transition"],
            }
        )

    asset_manifest = {
        "project": job.data["project"]["name"],
        "items": asset_items,
    }
    asset_manifest_file = jianying_dir / "asset_manifest.json"
    asset_manifest_file.write_text(json.dumps(asset_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    project_file_payload = {
        "project_name": job.data["project"]["name"],
        "draft_path": config["draft_path"],
        "resolution": config["resolution"],
        "fps": config["fps"],
        "timeline": timeline_items,
    }
    project_file = jianying_dir / "jianying_project.json"
    project_file.write_text(json.dumps(project_file_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    prompt_file = jianying_dir / "jianying_prompt.md"
    prompt_file.write_text(_build_prompt(job, timeline_items, config), encoding="utf-8")

    automation_status = "skipped"
    if not dry_run and config.get("automation_command"):
        automation_status = _run_automation(config["automation_command"], prompt_file)

    return {
        "prompt_file": str(prompt_file.resolve()),
        "project_file": str(project_file.resolve()),
        "asset_manifest_file": str(asset_manifest_file.resolve()),
        "automation_status": automation_status,
    }


def _build_prompt(job: JobContext, timeline_items: list[dict], config: dict) -> str:
    lines = [
        "# Jianying automation handoff",
        "",
        f"- Project: {job.data['project']['name']}",
        f"- Draft path: {config['draft_path'] or '<configure draft_path in config/jianying.json>'}",
        f"- Resolution: {config['resolution']}",
        f"- FPS: {config['fps']}",
        f"- Voice: {config['voice']}",
        f"- Transition: {config['transition']}",
        f"- Music: {config['music']}",
        "",
        "## Timeline items",
        "",
    ]
    for item in timeline_items:
        lines.append(
            f"- {item['scene_id']}: {item['title']} | status={item['status']} | media={item['media_path']}"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Import every ready media item in the listed order.",
            "- Keep pending items as placeholders until media rendering is complete.",
            "- Add subtitles, AI voice-over, transitions, and background music based on the project file.",
        ]
    )
    return "\n".join(lines) + "\n"


def _load_jianying_config(app: AppContext) -> dict:
    config_file = app.jianying_config_file
    if not config_file.exists():
        default_payload = {
            "draft_path": "",
            "automation_command": "",
            "resolution": "1080P",
            "fps": 30,
            "voice": "neutral-female",
            "transition": "fade",
            "music": "calm-instrumental",
        }
        config_file.write_text(json.dumps(default_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return default_payload
    config = read_json(config_file)
    claude_config = app.load_config(
        "claude-code.json",
        default={
            "enabled": False,
            "claude_command": "claude",
            "print_arg": "--print",
            "prompt_handoff_template": "{claude_command} {print_arg} < \"{prompt_file}\"",
        },
    )
    if not config.get("automation_command") and claude_config.get("enabled"):
        claude_command = env_or_value("VIDEO_FULL_CLAUDE_COMMAND", claude_config.get("claude_command", "claude"))
        config["automation_command"] = claude_config.get(
            "prompt_handoff_template",
            "{claude_command} {print_arg} < \"{prompt_file}\"",
        ).format(
            claude_command=claude_command,
            print_arg=claude_config.get("print_arg", "--print"),
            prompt_file="{prompt_file}",
        )
    return config


def _run_automation(command_template: str, prompt_file: Path) -> str:
    command = command_template.replace("{prompt_file}", str(prompt_file.resolve()))
    proc = subprocess.run(command, shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if proc.returncode == 0:
        return "executed"
    return f"failed: {proc.stderr.strip() or proc.stdout.strip() or proc.returncode}"
