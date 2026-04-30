#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.env_loader import load_dotenv
load_dotenv()

from commands.full import FullCommand
from commands.init import InitCommand
from commands.jianying import JianyingCommand
from commands.plan import PlanCommand
from commands.setup import SetupCommand
from commands.slides import SlidesCommand
from commands.video import VideoCommand
from commands.config import ConfigCommand
from core.app_context import AppContext


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="video-full",
        description="Generic CLI for presentation planning, LaTeX Beamer PDF generation, media tasks, and Jianying handoff.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  video-full init --project demo\n"
            "  video-full plan --project demo --source C:\\docs\n"
            "  video-full slides --config C:\\path\\project_job.json\n"
            "  video-full video --config C:\\path\\project_job.json --dry-run\n"
            "  video-full full --project demo --source C:\\docs\n"
        ),
    )
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parent),
        help="Application root. Defaults to the folder containing this CLI.",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    commands = [
        ConfigCommand(),
        SetupCommand(),
        InitCommand(),
        PlanCommand(),
        SlidesCommand(),
        VideoCommand(),
        JianyingCommand(),
        FullCommand(),
    ]
    for command in commands:
        command.register(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    app = AppContext(Path(args.root).resolve())
    try:
        return int(args.handler(args, app))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except Exception as exc:  # pragma: no cover - defensive top-level handler
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
