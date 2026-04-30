from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.app_context import AppContext
from core.utils import ensure_directory, safe_slug


class InitCommand:
    name = "init"

    def register(self, subparsers: argparse._SubParsersAction) -> None:
        parser = subparsers.add_parser(
            self.name,
            help="Initialize a generic project workspace.",
        )
        parser.add_argument("--project", required=True, help="Project name.")
        parser.add_argument(
            "--output",
            help="Workspace root. Defaults to <app>/output/<project-slug>.",
        )
        parser.set_defaults(handler=self.run)

    def run(self, args: argparse.Namespace, app: AppContext) -> int:
        slug = safe_slug(args.project)
        workspace = Path(args.output).resolve() if args.output else app.output_root / slug
        source_dir = workspace / "source"
        logs_dir = workspace / "logs"
        ensure_directory(source_dir)
        ensure_directory(logs_dir)

        template = {
            "project": {
                "name": args.project,
                "slug": slug,
                "author": "",
                "organization": "",
            },
            "notes": "Place your source documents under ./source and then run `video-full plan --project <name> --source <source-dir>`.",
        }
        template_path = workspace / "project_init.json"
        with template_path.open("w", encoding="utf-8") as handle:
            json.dump(template, handle, ensure_ascii=False, indent=2)

        (source_dir / "README.txt").write_text(
            "Put Markdown, text, JSON, and image files here before running the plan command.\n",
            encoding="utf-8",
        )

        print(f"Workspace: {workspace}")
        print(f"Config seed: {template_path}")
        print(f"Source folder: {source_dir}")
        return 0
