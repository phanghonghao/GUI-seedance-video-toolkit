from __future__ import annotations

import argparse

from core.app_context import AppContext
from core.job import create_job_from_source
from core.utils import pretty_json_path


class PlanCommand:
    name = "plan"

    def register(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            self.name,
            help="Read a source directory and create project_job.json.",
        )
        parser.add_argument("--source", required=True, help="Source document directory.")
        parser.add_argument("--project", required=True, help="Project name.")
        parser.add_argument("--output", help="Output root. Defaults to <app>/output.")
        parser.add_argument("--author", default="", help="Optional author name.")
        parser.add_argument("--organization", default="", help="Optional organization.")
        parser.add_argument("--theme-color", default="#1F4E79", help="Primary theme color.")
        parser.add_argument("--dry-run", action="store_true", help="Plan only; do not call external providers later.")
        parser.set_defaults(handler=self.run)

    def run(self, args: argparse.Namespace, app: AppContext) -> int:
        job = create_job_from_source(
            app=app,
            project_name=args.project,
            source_dir=args.source,
            output_root=args.output,
            author=args.author,
            organization=args.organization,
            theme_color=args.theme_color,
            dry_run=args.dry_run,
        )
        print(f"Created job file: {pretty_json_path(job.job_file)}")
        print(f"Run root: {job.run_root}")
        return 0
