from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from core.app_context import AppContext
from core.config_loader import env_or_value


@dataclass(slots=True)
class CheckResult:
    level: str
    area: str
    message: str


class ConfigCommand:
    name = "config"

    def register(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            self.name,
            help="Validate runtime configuration, local commands, and optional providers.",
        )
        parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Treat optional missing integrations as failures.",
        )
        parser.set_defaults(handler=self.run)

    def run(self, args: argparse.Namespace, app: AppContext) -> int:
        results = []
        results.extend(_check_json_files(app))
        results.extend(_check_miktex(app))
        results.extend(_check_nodejs(app))
        results.extend(_check_jianying_editor(app))
        results.extend(_check_providers(app))
        results.extend(_check_jianying(app))

        if args.json:
            payload = {
                "results": [
                    {"level": item.level, "area": item.area, "message": item.message}
                    for item in results
                ]
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            for item in results:
                print(f"[{item.level}] {item.area}: {item.message}")

        failing_levels = {"FAIL"}
        if args.strict:
            failing_levels.add("WARN")
        return 1 if any(item.level in failing_levels for item in results) else 0


def _check_json_files(app: AppContext) -> list[CheckResult]:
    required = [
        "miktex.json",
        "nodejs.json",
        "providers.json",
        "jianying.json",
        "project-defaults.json",
    ]
    results: list[CheckResult] = []
    for name in required:
        path = app.config_dir / name
        if not path.exists():
            results.append(CheckResult("FAIL", "config", f"Missing {path}"))
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            results.append(CheckResult("FAIL", "config", f"Invalid JSON in {path}: {exc}"))
            continue
        results.append(CheckResult("OK", "config", f"Loaded {path.name}"))
    return results


def _check_miktex(app: AppContext) -> list[CheckResult]:
    config = app.load_config(
        "miktex.json",
        default={
            "xelatex_command": "xelatex",
            "version_arg": "--version",
            "distribution": "MiKTeX",
        },
    )
    command = str(env_or_value("VIDEO_FULL_XELATEX_COMMAND", config.get("xelatex_command", "xelatex"))).strip()
    version_arg = str(config.get("version_arg", "--version")).strip() or "--version"
    minimum_major = int(str(config.get("minimum_major_version", "0")).strip() or 0)
    return _check_command(
        area="miktex",
        command=command,
        version_arg=version_arg,
        minimum_major=minimum_major,
        optional=False,
        success_prefix=f"{config.get('distribution', 'XeLaTeX')} command ready",
    )


def _check_nodejs(app: AppContext) -> list[CheckResult]:
    config = app.load_config(
        "nodejs.json",
        default={
            "node_command": "node",
            "npm_command": "npm",
            "npx_command": "npx",
            "minimum_version": "18",
            "node_version_arg": "--version",
            "npm_version_arg": "--version",
            "npx_version_arg": "--version",
        },
    )
    minimum_major = int(str(config.get("minimum_version", "18")).strip() or 18)
    results = []
    results.extend(
        _check_command(
            area="nodejs",
            command=str(config.get("node_command", "node")).strip(),
            version_arg=str(config.get("node_version_arg", "--version")).strip() or "--version",
            minimum_major=minimum_major,
            optional=False,
            success_prefix="Node.js command ready",
        )
    )
    results.extend(
        _check_command(
            area="nodejs",
            command=str(config.get("npm_command", "npm")).strip(),
            version_arg=str(config.get("npm_version_arg", "--version")).strip() or "--version",
            minimum_major=0,
            optional=False,
            success_prefix="npm command ready",
        )
    )
    results.extend(
        _check_command(
            area="nodejs",
            command=str(config.get("npx_command", "npx")).strip(),
            version_arg=str(config.get("npx_version_arg", "--version")).strip() or "--version",
            minimum_major=0,
            optional=True,
            success_prefix="npx command ready",
        )
    )
    return results


def _check_jianying_editor(app: AppContext) -> list[CheckResult]:
    scripts_dir = app.root / "libs" / "jianying-editor" / "scripts"
    wrapper = scripts_dir / "jy_wrapper.py"
    results = []
    if wrapper.is_file():
        results.append(CheckResult("OK", "jianying-editor", f"Submodule ready: {scripts_dir}"))
    else:
        results.append(
            CheckResult(
                "WARN",
                "jianying-editor",
                "libs/jianying-editor submodule not found. Run: git submodule update --init --recursive",
            )
        )
    return results


def _check_providers(app: AppContext) -> list[CheckResult]:
    config = app.load_config("providers.json", default={})
    image = config.get("image", {})
    video = config.get("video", {})
    results = []
    image_env = image.get("env", {})
    image_api_key = str(env_or_value(image_env.get("api_key", "VIDEO_FULL_IMAGE_API_KEY"), image.get("api_key", ""))).strip()
    image_base_url = str(env_or_value(image_env.get("base_url", "VIDEO_FULL_IMAGE_API_BASE"), image.get("base_url", ""))).strip()
    if image_api_key and image_base_url:
        results.append(CheckResult("OK", "providers", f"Image provider configured with model {image.get('model', 'gpt-image-1')}"))
    else:
        results.append(CheckResult("WARN", "providers", "Image provider is not fully configured; text-to-image and image-to-image will use placeholders"))

    video_env = video.get("env", {})
    video_api_key = str(env_or_value(video_env.get("api_key", "VIDEO_FULL_VIDEO_API_KEY"), video.get("api_key", ""))).strip()
    video_task_url = str(env_or_value(video_env.get("task_url", "VIDEO_FULL_VIDEO_TASK_URL"), video.get("task_url", ""))).strip()
    video_status_url = str(env_or_value(video_env.get("status_url", "VIDEO_FULL_VIDEO_STATUS_URL"), video.get("status_url", ""))).strip()
    if video_api_key and video_task_url and video_status_url:
        results.append(CheckResult("OK", "providers", f"Video provider configured with model {video.get('model', 'generic-video-model')}"))
    else:
        results.append(CheckResult("WARN", "providers", "Video provider is not fully configured; text-to-video and image-to-video will use placeholders"))
    return results


def _check_jianying(app: AppContext) -> list[CheckResult]:
    config = app.load_config(
        "jianying.json",
        default={
            "draft_path": "",
            "automation_command": "",
            "resolution": "1080P",
            "fps": 30,
        },
    )
    results = []
    draft_path = str(config.get("draft_path", "")).strip()
    if draft_path:
        draft_dir = Path(draft_path)
        if draft_dir.exists():
            results.append(CheckResult("OK", "jianying", f"Draft path exists: {draft_dir}"))
        else:
            results.append(CheckResult("WARN", "jianying", f"Draft path does not exist yet: {draft_dir}"))
    else:
        results.append(CheckResult("WARN", "jianying", "draft_path is empty in config/jianying.json"))

    results.append(
        CheckResult(
            "OK",
            "jianying",
            f"Output defaults: resolution={config.get('resolution', '1080P')}, fps={config.get('fps', 30)}",
        )
    )
    return results


def _check_command(
    area: str,
    command: str,
    version_arg: str,
    minimum_major: int,
    optional: bool,
    success_prefix: str,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    if not command:
        level = "WARN" if optional else "FAIL"
        results.append(CheckResult(level, area, "Command is empty"))
        return results

    resolved = shutil.which(command) or (command if Path(command).exists() else "")
    if not resolved:
        level = "WARN" if optional else "FAIL"
        results.append(CheckResult(level, area, f"Command not found: {command}"))
        return results

    try:
        proc = subprocess.run(
            [resolved, version_arg],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
        )
    except OSError as exc:
        level = "WARN" if optional else "FAIL"
        results.append(CheckResult(level, area, f"Failed to run {command}: {exc}"))
        return results

    if proc.returncode != 0:
        level = "WARN" if optional else "FAIL"
        stderr = (proc.stderr or proc.stdout).strip() or str(proc.returncode)
        results.append(CheckResult(level, area, f"Version check failed for {command}: {stderr}"))
        return results

    version_text = (proc.stdout or proc.stderr).strip().splitlines()
    version_line = version_text[0].strip() if version_text else "unknown"
    parsed_major = _extract_major_version(version_line)
    if minimum_major and parsed_major is not None and parsed_major < minimum_major:
        results.append(
            CheckResult(
                "FAIL",
                area,
                f"{command} version is below required major version {minimum_major}: {version_line}",
            )
        )
        return results

    results.append(CheckResult("OK", area, f"{success_prefix}: {resolved} ({version_line})"))
    return results


def _extract_major_version(version_line: str) -> int | None:
    text = version_line.strip()
    if text.startswith("v"):
        text = text[1:]
    digits = []
    for char in text:
        if char.isdigit():
            digits.append(char)
            continue
        if digits:
            break
    if not digits:
        return None
    return int("".join(digits))
