from __future__ import annotations

import argparse

from core.app_context import AppContext
from core.job import ensure_job
from core.latex_builder import build_slides


class SlidesCommand:
    name = "slides"

    def register(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            self.name,
            help="Render and compile the generic LaTeX Beamer deck.",
        )
        parser.add_argument("--config", help="Path to project_job.json.")
        parser.add_argument("--source", help="Source directory when no config is provided.")
        parser.add_argument("--project", help="Project name when no config is provided.")
        parser.add_argument("--output", help="Output root. Defaults to <app>/output.")
        parser.add_argument("--dry-run", action="store_true", help="Render .tex but skip XeLaTeX compilation.")
        parser.set_defaults(handler=self.run)

    def run(self, args: argparse.Namespace, app: AppContext) -> int:
        job = ensure_job(app, args)
        result = build_slides(app, job, dry_run=args.dry_run)
        print(f"TeX file: {result['tex_file']}")
        if result.get("pdf_file"):
            print(f"PDF file: {result['pdf_file']}")
        else:
            print("PDF build skipped.")
        return 0
