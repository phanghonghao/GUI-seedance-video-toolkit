"""Interactive setup wizard — video-full setup."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from core.app_context import AppContext


class SetupCommand:
    name = "setup"

    def register(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            self.name,
            help="Interactive setup wizard: detect tools, configure API keys, write config files.",
        )
        parser.set_defaults(handler=self.run)

    def run(self, args: argparse.Namespace, app: AppContext) -> int:
        print("=" * 50)
        print("  video-full setup wizard")
        print("=" * 50)
        print()

        env_lines: list[str] = []

        # 1. Jianying Pro draft path
        _setup_jianying_draft_path(app, env_lines)

        # 2. MiKTeX / xelatex
        _setup_miktex(app)

        # 3. Node.js
        _setup_nodejs(app)

        # 4. API keys
        _setup_api_keys(app, env_lines)

        # 5. Write .env
        _write_env(app, env_lines)

        # 6. Check jianying-editor submodule
        _check_submodule(app)

        # 7. Pip install reminder
        _pip_reminder(app)

        # 8. Run config check
        print()
        print("--- Running config check ---")
        from commands.config import ConfigCommand
        return ConfigCommand().run(
            argparse.Namespace(json=False, strict=False),
            app,
        )


# ── helpers ──────────────────────────────────────────────────────────


def _prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        raw = input(f"  {label}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return raw or default


def _detect_jianying_draft_path() -> str:
    local_app = os.environ.get("LOCALAPPDATA", "")
    if not local_app:
        return ""
    base = Path(local_app) / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft"
    if base.is_dir():
        return str(base)
    return ""


def _setup_jianying_draft_path(app: AppContext, env_lines: list[str]) -> None:
    print("[1/4] Jianying Pro draft path")
    detected = _detect_jianying_draft_path()
    value = _prompt("Draft path", detected)
    config_path = app.config_dir / "jianying.json"
    config = _load_or_create(config_path, {
        "draft_path": "",
        "resolution": "1080P",
        "fps": 30,
        "voice": "neutral-female",
        "transition": "fade",
        "music": "calm-instrumental",
        "subtitles": True,
    })
    config["draft_path"] = value
    _write_json(config_path, config)
    print(f"  -> saved to {config_path}")
    print()


def _setup_miktex(app: AppContext) -> None:
    print("[2/4] MiKTeX / XeLaTeX")
    resolved = shutil.which("xelatex") or ""
    value = _prompt("xelatex command", resolved or "xelatex")
    config_path = app.config_dir / "miktex.json"
    config = _load_or_create(config_path, {
        "xelatex_command": "xelatex",
        "version_arg": "--version",
        "compile_flags": ["-interaction=nonstopmode", "-halt-on-error"],
        "runs": 2,
        "output_pdf_name": "main.pdf",
        "distribution": "MiKTeX",
        "minimum_major_version": 0,
    })
    config["xelatex_command"] = value
    _write_json(config_path, config)
    print(f"  -> saved to {config_path}")
    print()


def _setup_nodejs(app: AppContext) -> None:
    print("[3/4] Node.js")
    node = shutil.which("node") or "node"
    npm = shutil.which("npm") or "npm"
    npx = shutil.which("npx") or "npx"
    config_path = app.config_dir / "nodejs.json"
    config = _load_or_create(config_path, {
        "node_command": "node",
        "npm_command": "npm",
        "npx_command": "npx",
        "node_version_arg": "--version",
        "npm_version_arg": "--version",
        "npx_version_arg": "--version",
        "minimum_version": "18",
        "package_manager": "npm",
    })
    config["node_command"] = _prompt("node command", node)
    config["npm_command"] = _prompt("npm command", npm)
    config["npx_command"] = _prompt("npx command", npx)
    _write_json(config_path, config)
    print(f"  -> saved to {config_path}")
    print()


def _setup_api_keys(app: AppContext, env_lines: list[str]) -> None:
    print("[4/4] API keys (leave blank to skip)")
    config_path = app.config_dir / "providers.json"
    config = _load_or_create(config_path, {
        "image": {
            "provider": "openai-compatible",
            "api_key": "",
            "base_url": "",
            "model": "Doubao-Seedream-3.0-T2I",
            "size": "1536x1024",
        },
        "video": {
            "provider": "generic-task-api",
            "api_key": "",
            "task_url": "",
            "status_url": "",
            "model": "Doubao-Seedance-1.0-Pro",
            "poll_seconds": 10,
            "max_polls": 60,
        },
    })

    img_key = _prompt("Image API key", "")
    img_url = _prompt("Image base URL", "")
    config["image"]["api_key"] = img_key
    config["image"]["base_url"] = img_url

    vid_key = _prompt("Video API key", "")
    vid_url = _prompt("Video task URL", "")
    config["video"]["api_key"] = vid_key
    config["video"]["task_url"] = vid_url
    config["video"]["status_url"] = vid_url

    _write_json(config_path, config)

    # Prefer .env for secrets
    if img_key:
        env_lines.append(f"VIDEO_FULL_IMAGE_API_KEY={img_key}")
    if img_url:
        env_lines.append(f"VIDEO_FULL_IMAGE_API_BASE={img_url}")
    if vid_key:
        env_lines.append(f"VIDEO_FULL_VIDEO_API_KEY={vid_key}")
    if vid_url:
        env_lines.append(f"VIDEO_FULL_VIDEO_TASK_URL={vid_url}")
        env_lines.append(f"VIDEO_FULL_VIDEO_STATUS_URL={vid_url}")

    print(f"  -> saved to {config_path}")
    print()


def _write_env(app: AppContext, lines: list[str]) -> None:
    if not lines:
        return
    env_path = app.root / ".env"
    existing: list[str] = []
    if env_path.is_file():
        existing = env_path.read_text(encoding="utf-8").splitlines()
    # Merge: keep existing lines that aren't being overwritten
    new_keys = {line.split("=", 1)[0] for line in lines if "=" in line}
    merged = [l for l in existing if l.split("=", 1)[0] not in new_keys]
    merged.extend(lines)
    env_path.write_text("\n".join(merged) + "\n", encoding="utf-8")
    print(f"  -> .env written ({len(lines)} entries)")
    print()


def _check_submodule(app: AppContext) -> None:
    wrapper = app.root / "libs" / "jianying-editor" / "scripts" / "jy_wrapper.py"
    if wrapper.is_file():
        print("  [OK] jianying-editor submodule is present")
    else:
        print("  [!!] jianying-editor submodule missing!")
        print("       Run: git submodule update --init --recursive")
    print()


def _pip_reminder(app: AppContext) -> None:
    req = app.root / "requirements.txt"
    if req.is_file():
        print("  To install Python dependencies:")
        print("    pip install -r requirements.txt")
    print()


def _load_or_create(path: Path, default: dict) -> dict:
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return dict(default)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
