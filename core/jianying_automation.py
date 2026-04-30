"""Direct Jianying draft builder — no Claude Code dependency."""
from __future__ import annotations

import importlib.util
import io
import os
import sys
from pathlib import Path


def _resolve_jy_wrapper():
    """Load jy_wrapper via importlib to avoid core/ namespace collision."""
    project_root = Path(__file__).resolve().parent.parent
    skill_root = project_root / "libs" / "jianying-editor"
    scripts_dir = skill_root / "scripts"
    vendor_dir = scripts_dir / "vendor"
    wrapper_file = scripts_dir / "jy_wrapper.py"
    if not wrapper_file.is_file():
        raise FileNotFoundError(
            f"jianying-editor submodule not found at {scripts_dir}. "
            "Run: git submodule update --init --recursive"
        )

    # Set JY_SKILL_ROOT so the skill's own env_setup finds itself
    os.environ["JY_SKILL_ROOT"] = str(skill_root)

    # Inject paths needed by jy_wrapper and its transitive imports
    for d in (str(vendor_dir), str(scripts_dir)):
        if d not in sys.path:
            sys.path.insert(0, d)

    # The submodule's core/ has no __init__.py — it relies on implicit
    # namespace packages.  Our top-level core/__init__.py takes priority
    # unless we remove both the sys.modules cache AND any sys.path entry
    # pointing at our project root (including "" which resolves to CWD).
    root_str = str(project_root)
    removed_paths: list[tuple[int, str]] = []
    for i in range(len(sys.path) - 1, -1, -1):
        p = sys.path[i]
        if p in ("", root_str):
            removed_paths.append((i, sys.path.pop(i)))

    saved_modules = {k: v for k, v in list(sys.modules.items()) if k == "core" or k.startswith("core.")}
    for k in saved_modules:
        sys.modules.pop(k, None)

    try:
        spec = importlib.util.spec_from_file_location("jy_wrapper", str(wrapper_file))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        # Restore sys.path entries and our core package
        for i, p in reversed(removed_paths):
            sys.path.insert(i, p)
        for k, v in saved_modules.items():
            sys.modules[k] = v

    return mod.JyProject


def _fix_stdout_encoding() -> None:
    """Reconfigure stdout/stderr to utf-8 on Windows to avoid gbk emoji errors."""
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def build_jianying_draft(
    project_name: str,
    draft_path: str,
    timeline_items: list[dict],
    config: dict,
) -> dict:
    """Build a Jianying Pro draft directly via JyProject.

    Parameters
    ----------
    project_name : str
        Name shown in Jianying Pro.
    draft_path : str
        Root directory of Jianying draft storage.
    timeline_items : list[dict]
        Each item: {scene_id, title, media_path, status, voice, transition}.
    config : dict
        Jianying config (resolution, fps, voice, transition, music, subtitles).

    Returns
    -------
    dict
        {"status": "ok", "draft_dir": str} on success,
        {"status": "error", "message": str} on failure.
    """
    try:
        JyProject = _resolve_jy_wrapper()
    except FileNotFoundError as exc:
        return {"status": "error", "message": str(exc)}

    # Ensure stdout can handle emoji / CJK chars (Windows gbk default)
    _fix_stdout_encoding()

    resolution = config.get("resolution", "1080P")
    width, height = {"1080P": (1920, 1080), "4K": (3840, 2160)}.get(resolution, (1920, 1080))

    try:
        project = JyProject(
            project_name=project_name,
            width=width,
            height=height,
            drafts_root=draft_path,
            overwrite=True,
        )
    except Exception as exc:
        return {"status": "error", "message": f"Failed to create JyProject: {exc}"}

    ready_items = [item for item in timeline_items if item.get("status") == "ready"]
    if not ready_items:
        try:
            result = project.save()
            return {"status": "ok", "draft_dir": result.get("draft_path", "")}
        except Exception as exc:
            return {"status": "error", "message": f"Failed to save empty project: {exc}"}

    for item in ready_items:
        media_path = item["media_path"]
        try:
            current_end = project.get_track_duration("VideoTrack")
            project.add_media_safe(
                media_path=media_path,
                start_time=current_end,
                track_name="VideoTrack",
            )
        except Exception as exc:
            print(f"  [WARN] Could not add media {media_path}: {exc}")

    if config.get("subtitles", True):
        current_end = 0
        for item in ready_items:
            try:
                project.add_text_simple(
                    text=item.get("title", ""),
                    start_time=current_end,
                    duration="3s",
                    track_name="Subtitles",
                )
            except Exception:
                pass
            current_end = project.get_track_duration("VideoTrack")

    try:
        result = project.save()
        return {"status": "ok", "draft_dir": result.get("draft_path", "")}
    except Exception as exc:
        return {"status": "error", "message": f"Failed to save project: {exc}"}
