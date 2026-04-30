from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from .app_context import AppContext
from .content import scan_source_directory
from .utils import ensure_directory, read_json, safe_slug, timestamp, write_json


@dataclass(slots=True)
class JobContext:
    app: AppContext
    job_file: Path
    data: dict

    @property
    def run_root(self) -> Path:
        return Path(self.data["outputs"]["root"])


def create_job_from_source(
    app: AppContext,
    project_name: str,
    source_dir: str,
    output_root: str | None = None,
    author: str = "",
    organization: str = "",
    theme_color: str = "#1F4E79",
    dry_run: bool = False,
) -> JobContext:
    project_defaults = app.load_config("project-defaults.json", default={})
    source_path = Path(source_dir).resolve()
    if not source_path.exists() or not source_path.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_path}")

    scan = scan_source_directory(source_path)
    slug = safe_slug(project_name)
    run_root = ensure_directory(
        (Path(output_root).resolve() if output_root else app.output_root) / slug / timestamp()
    )
    job_dir = ensure_directory(run_root / "job")
    slides_dir = ensure_directory(run_root / "slides")
    media_dir = ensure_directory(run_root / "media")
    jianying_dir = ensure_directory(run_root / "jianying")
    logs_dir = ensure_directory(run_root / "logs")

    section_titles = {
        "background": "Background and Problem",
        "solution": "Solution Overview",
        "features": "Core Features",
        "technology": "Technical Approach",
        "results": "Results and Value",
        "plan": "Roadmap and Next Steps",
    }

    slides_sections = [
        {
            "key": key,
            "title": section_titles[key],
            "bullets": scan.sections[key][:5],
        }
        for key in ("background", "solution", "features", "technology", "results", "plan")
    ]

    primary_image = str(scan.image_files[0].resolve()) if scan.image_files else ""
    secondary_image = str(scan.image_files[1].resolve()) if len(scan.image_files) > 1 else primary_image

    media_scenes = [
        {
            "id": "scene-01",
            "title": "Project Overview Visual",
            "mode": "text-to-image",
            "prompt": f"Create a clean presentation cover visual for {project_name}. Focus on the main solution and the project value.",
            "source_image": "",
            "output_file": str((media_dir / "scene-01-overview.png").resolve()),
        },
        {
            "id": "scene-02",
            "title": "Problem Storyboard",
            "mode": "text-to-video",
            "prompt": f"Create a short presentation clip that visualizes the background, problem, and urgency for {project_name}.",
            "source_image": "",
            "output_file": str((media_dir / "scene-02-problem.mp4").resolve()),
        },
        {
            "id": "scene-03",
            "title": "Solution Motion Clip",
            "mode": "image-to-video",
            "prompt": f"Animate the main solution of {project_name} in a concise explainer clip.",
            "source_image": primary_image,
            "output_file": str((media_dir / "scene-03-solution.mp4").resolve()),
        },
        {
            "id": "scene-04",
            "title": "Feature Illustration",
            "mode": "text-to-image",
            "prompt": f"Create an illustration that summarizes the core features of {project_name} for a presentation slide.",
            "source_image": "",
            "output_file": str((media_dir / "scene-04-features.png").resolve()),
        },
        {
            "id": "scene-05",
            "title": "Technical Diagram Refresh",
            "mode": "image-to-image",
            "prompt": f"Restyle a technical diagram into a presentation-ready board for {project_name}.",
            "source_image": secondary_image,
            "output_file": str((media_dir / "scene-05-technology.png").resolve()),
        },
        {
            "id": "scene-06",
            "title": "Roadmap Clip",
            "mode": "text-to-video",
            "prompt": f"Create a concise roadmap clip for the next steps and delivery plan of {project_name}.",
            "source_image": "",
            "output_file": str((media_dir / "scene-06-roadmap.mp4").resolve()),
        },
    ]

    slides_defaults = project_defaults.get("slides", {})
    slide_theme_defaults = slides_defaults.get("theme", {})
    slide_compile_defaults = slides_defaults.get("compile", {})
    jianying_defaults = project_defaults.get("jianying", {})

    data = {
        "project": {
            "name": project_name,
            "slug": slug,
            "author": author,
            "organization": organization,
            "title_hint": scan.title_hint,
        },
        "sources": {
            "root": str(source_path),
            "documents": [str(path.resolve()) for path in scan.text_files],
            "images": [str(path.resolve()) for path in scan.image_files],
        },
        "slides": {
            "title": project_name,
            "subtitle": scan.title_hint if scan.title_hint != project_name else "",
            "author": author,
            "organization": organization,
            "theme": {
                "primary_color": theme_color or slide_theme_defaults.get("primary_color", "#1F4E79"),
                "accent_color": slide_theme_defaults.get("accent_color", "#D9E7F5"),
            },
            "compile": {
                "engine": slide_compile_defaults.get("engine", "xelatex"),
                "runs": int(slide_compile_defaults.get("runs", 2)),
            },
            "sections": slides_sections,
        },
        "media": {
            "dry_run": dry_run,
            "scenes": media_scenes,
        },
        "jianying": {
            "voice": jianying_defaults.get("voice", "neutral-female"),
            "subtitles": bool(jianying_defaults.get("subtitles", True)),
            "transition": jianying_defaults.get("transition", "fade"),
            "music": jianying_defaults.get("music", "calm-instrumental"),
            "draft_path": "",
            "automation_command": "",
        },
        "outputs": {
            "root": str(run_root.resolve()),
            "job_dir": str(job_dir.resolve()),
            "slides_dir": str(slides_dir.resolve()),
            "media_dir": str(media_dir.resolve()),
            "jianying_dir": str(jianying_dir.resolve()),
            "logs_dir": str(logs_dir.resolve()),
        },
    }

    job_file = job_dir / "project_job.json"
    write_json(job_file, data)
    return JobContext(app=app, job_file=job_file, data=data)


def load_job(app: AppContext, config_path: str) -> JobContext:
    job_file = Path(config_path).resolve()
    return JobContext(app=app, job_file=job_file, data=read_json(job_file))


def ensure_job(app: AppContext, args: SimpleNamespace) -> JobContext:
    if getattr(args, "config", None):
        return load_job(app, args.config)
    if not getattr(args, "source", None) or not getattr(args, "project", None):
        raise ValueError("Provide --config or both --source and --project.")
    return create_job_from_source(
        app=app,
        project_name=args.project,
        source_dir=args.source,
        output_root=getattr(args, "output", None),
        dry_run=bool(getattr(args, "dry_run", False)),
    )
