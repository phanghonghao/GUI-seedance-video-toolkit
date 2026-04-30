from __future__ import annotations

import argparse

from core.app_context import AppContext
from core.job import ensure_job
from core.media_pipeline import run_media_pipeline


class VideoCommand:
    name = "video"

    def register(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            self.name,
            help="Run the generic media pipeline.",
        )
        parser.add_argument("--config", help="Path to project_job.json.")
        parser.add_argument("--source", help="Source directory when no config is provided.")
        parser.add_argument("--project", help="Project name when no config is provided.")
        parser.add_argument("--output", help="Output root. Defaults to <app>/output.")
        parser.add_argument("--dry-run", action="store_true", help="Do not call external providers.")
        parser.set_defaults(handler=self.run)

    def run(self, args: argparse.Namespace, app: AppContext) -> int:
        job = ensure_job(app, args)
        result = run_media_pipeline(app, job, dry_run=args.dry_run)
        print(f"Media manifest: {result['manifest_file']}")
        print(f"Generated items: {result['generated_count']}")
        print(f"Planned items: {result['planned_count']}")
        return 0
