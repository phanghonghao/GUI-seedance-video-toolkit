from __future__ import annotations

import json
import zlib
from pathlib import Path

from integrations.openai_image import OpenAIImageClient
from integrations.task_video import GenericTaskVideoClient

from .app_context import AppContext
from .job import JobContext
from .utils import ensure_directory


def run_media_pipeline(app: AppContext, job: JobContext, dry_run: bool = False) -> dict:
    media_dir = ensure_directory(Path(job.data["outputs"]["media_dir"]))
    logs_dir = ensure_directory(Path(job.data["outputs"]["logs_dir"]))
    image_client = OpenAIImageClient.from_environment()
    video_client = GenericTaskVideoClient.from_environment()

    items: list[dict] = []
    generated_count = 0
    planned_count = 0

    for scene in job.data["media"]["scenes"]:
        mode = scene["mode"]
        output_path = Path(scene["output_file"])
        item = {
            "id": scene["id"],
            "title": scene["title"],
            "mode": mode,
            "prompt": scene["prompt"],
            "source_image": scene.get("source_image", ""),
            "output_file": str(output_path.resolve()),
            "status": "planned",
        }

        if dry_run:
            _create_placeholder(item, output_path)
            _write_task_file(media_dir, scene["id"], item)
            planned_count += 1
            items.append(item)
            continue

        if mode in {"text-to-image", "image-to-image"} and image_client.is_configured:
            if mode == "text-to-image" or not item["source_image"]:
                image_client.generate_text_to_image(scene["prompt"], output_path)
            else:
                image_client.generate_image_to_image(scene["prompt"], Path(item["source_image"]), output_path)
            item["status"] = "generated"
            generated_count += 1
        elif mode in {"text-to-video", "image-to-video"} and video_client.is_configured:
            if mode == "text-to-video" or not item["source_image"]:
                video_client.generate_text_to_video(scene["prompt"], output_path)
            else:
                video_client.generate_image_to_video(scene["prompt"], Path(item["source_image"]), output_path)
            item["status"] = "generated"
            generated_count += 1
        else:
            _create_placeholder(item, output_path)
            item["status"] = "planned"
            planned_count += 1

        _write_task_file(media_dir, scene["id"], item)
        items.append(item)

    manifest = {
        "items": items,
        "generated_count": generated_count,
        "planned_count": planned_count,
    }
    manifest_file = media_dir / "media_manifest.json"
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    log_file = logs_dir / "media_pipeline.log"
    log_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "manifest_file": str(manifest_file.resolve()),
        "generated_count": generated_count,
        "planned_count": planned_count,
    }


def _write_task_file(media_dir: Path, scene_id: str, payload: dict) -> None:
    task_file = media_dir / f"{scene_id}.task.json"
    task_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _create_placeholder(item: dict, output_path: Path) -> None:
    ensure_directory(output_path.parent)
    suffix = output_path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
        output_path.write_bytes(_build_placeholder_png())
        return

    note = {
        "status": "planned",
        "message": "No external video provider is configured. This file marks a pending render target.",
        "expected_output": str(output_path.resolve()),
        "prompt": item["prompt"],
    }
    output_path.with_suffix(output_path.suffix + ".pending.json").write_text(
        json.dumps(note, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _build_placeholder_png(width: int = 1280, height: int = 720) -> bytes:
    def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return len(data).to_bytes(4, "big") + chunk_type + data + crc.to_bytes(4, "big")

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = png_chunk(b"IHDR", width.to_bytes(4, "big") + height.to_bytes(4, "big") + b"\x08\x02\x00\x00\x00")

    row = b"\x00" + (b"\xD9\xE7\xF5" * width)
    image_data = row * height
    idat = png_chunk(b"IDAT", zlib.compress(image_data, level=9))
    iend = png_chunk(b"IEND", b"")
    return signature + ihdr + idat + iend
