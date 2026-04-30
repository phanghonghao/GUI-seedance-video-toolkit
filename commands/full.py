from __future__ import annotations

import argparse
import json

from core.app_context import AppContext
from core.job import ensure_job
from core.jianying_pipeline import run_jianying_pipeline
from core.latex_builder import build_slides
from core.media_pipeline import run_media_pipeline
from core.utils import ensure_directory


class FullCommand:
    name = "full"

    def register(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            self.name,
            help="Run plan, slides, media, and Jianying steps in sequence.",
        )
        parser.add_argument("--config", help="Path to project_job.json.")
        parser.add_argument("--source", help="Source directory when no config is provided.")
        parser.add_argument("--project", help="Project name when no config is provided.")
        parser.add_argument("--output", help="Output root. Defaults to <app>/output.")
        parser.add_argument("--dry-run", action="store_true", help="Do not call external providers or automation.")
        parser.set_defaults(handler=self.run)

    def run(self, args: argparse.Namespace, app: AppContext) -> int:
        job = ensure_job(app, args)
        slides_result = build_slides(app, job, dry_run=args.dry_run)
        media_result = run_media_pipeline(app, job, dry_run=args.dry_run)
        jianying_result = run_jianying_pipeline(app, job, dry_run=args.dry_run)

        logs_dir = ensure_directory(job.run_root / "logs")
        summary = {
            "job_file": str(job.job_file),
            "slides": slides_result,
            "media": media_result,
            "jianying": jianying_result,
        }
        summary_path = logs_dir / "execution_summary.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Summary file: {summary_path}")
        return 0
