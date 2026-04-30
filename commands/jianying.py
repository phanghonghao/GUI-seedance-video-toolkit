from __future__ import annotations

import argparse

from core.app_context import AppContext
from core.job import ensure_job
from core.jianying_pipeline import run_jianying_pipeline


class JianyingCommand:
    name = "jianying"

    def register(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            self.name,
            help="Generate Jianying draft and project files via direct JyProject API.",
        )
        parser.add_argument("--config", help="Path to project_job.json.")
        parser.add_argument("--source", help="Source directory when no config is provided.")
        parser.add_argument("--project", help="Project name when no config is provided.")
        parser.add_argument("--output", help="Output root. Defaults to <app>/output.")
        parser.add_argument("--dry-run", action="store_true", help="Generate files only, skip draft creation.")
        parser.set_defaults(handler=self.run)

    def run(self, args: argparse.Namespace, app: AppContext) -> int:
        job = ensure_job(app, args)
        result = run_jianying_pipeline(app, job, dry_run=args.dry_run)
        print(f"Project file: {result['project_file']}")
        print(f"Asset manifest: {result['asset_manifest_file']}")
        if result.get("draft_dir"):
            print(f"Draft directory: {result['draft_dir']}")
        print(f"Automation status: {result['automation_status']}")
        return 0
