from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config_loader import load_json_config
from .utils import ensure_directory


@dataclass(slots=True)
class AppContext:
    root: Path

    @property
    def commands_dir(self) -> Path:
        return self.root / "commands"

    @property
    def config_dir(self) -> Path:
        return ensure_directory(self.root / "config")

    @property
    def output_root(self) -> Path:
        return ensure_directory(self.root / "output")

    @property
    def template_dir(self) -> Path:
        return self.root / "templates"

    @property
    def latex_template(self) -> Path:
        return self.template_dir / "latex-beamer" / "main.tex.tpl"

    @property
    def jianying_config_file(self) -> Path:
        return self.config_dir / "jianying.json"

    @property
    def miktex_config_file(self) -> Path:
        return self.config_dir / "miktex.json"

    @property
    def nodejs_config_file(self) -> Path:
        return self.config_dir / "nodejs.json"

    @property
    def claude_code_config_file(self) -> Path:
        return self.config_dir / "claude-code.json"

    @property
    def providers_config_file(self) -> Path:
        return self.config_dir / "providers.json"

    @property
    def project_defaults_config_file(self) -> Path:
        return self.config_dir / "project-defaults.json"

    def load_config(self, file_name: str, default: dict | None = None) -> dict:
        return load_json_config(self.config_dir / file_name, default=default)
