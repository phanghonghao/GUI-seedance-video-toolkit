from __future__ import annotations

import json
from pathlib import Path

from .app_context import AppContext
from .jianying_automation import build_jianying_draft
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

    automation_status = "skipped"
    draft_dir = ""
    if not dry_run and config.get("draft_path"):
        result = build_jianying_draft(
            project_name=job.data["project"]["name"],
            draft_path=config["draft_path"],
            timeline_items=timeline_items,
            config=config,
        )
        automation_status = result["status"]
        draft_dir = result.get("draft_dir", "")
        if result["status"] == "error":
            automation_status = f"error: {result['message']}"

    return {
        "project_file": str(project_file.resolve()),
        "asset_manifest_file": str(asset_manifest_file.resolve()),
        "automation_status": automation_status,
        "draft_dir": draft_dir,
    }


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
            "subtitles": True,
        }
        config_file.write_text(json.dumps(default_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return default_payload
    return read_json(config_file)
