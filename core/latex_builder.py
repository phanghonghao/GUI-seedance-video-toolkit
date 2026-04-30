from __future__ import annotations

import subprocess
from pathlib import Path

from .app_context import AppContext
from .config_loader import env_or_value
from .job import JobContext
from .utils import latex_escape, normalize_file_uri


def build_slides(app: AppContext, job: JobContext, dry_run: bool = False) -> dict:
    slides_dir = Path(job.data["outputs"]["slides_dir"])
    logs_dir = Path(job.data["outputs"]["logs_dir"])
    template = app.latex_template.read_text(encoding="utf-8")

    body = _render_body(job)
    theme = job.data["slides"]["theme"]
    rendered = (
        template.replace("<<TITLE>>", latex_escape(job.data["slides"]["title"]))
        .replace("<<SUBTITLE>>", latex_escape(job.data["slides"].get("subtitle", "")))
        .replace("<<AUTHOR>>", latex_escape(job.data["slides"].get("author", "")))
        .replace("<<ORG>>", latex_escape(job.data["slides"].get("organization", "")))
        .replace("<<PRIMARY_COLOR>>", theme["primary_color"].lstrip("#"))
        .replace("<<ACCENT_COLOR>>", theme["accent_color"].lstrip("#"))
        .replace("<<BODY>>", body)
    )

    tex_file = slides_dir / "main.tex"
    tex_file.write_text(rendered, encoding="utf-8")

    result = {"tex_file": str(tex_file.resolve()), "pdf_file": ""}
    if dry_run:
        return result

    log_path = logs_dir / "slides_build.log"
    miktex_config = app.load_config(
        "miktex.json",
        default={
            "xelatex_command": "xelatex",
            "compile_flags": ["-interaction=nonstopmode", "-halt-on-error"],
            "runs": 2,
            "output_pdf_name": "main.pdf",
        },
    )
    xelatex_command = env_or_value("VIDEO_FULL_XELATEX_COMMAND", miktex_config["xelatex_command"])
    compile_flags = list(miktex_config.get("compile_flags", ["-interaction=nonstopmode", "-halt-on-error"]))
    compile_runs = int(job.data["slides"]["compile"].get("runs", miktex_config.get("runs", 2)))
    for _ in range(max(1, compile_runs)):
        proc = subprocess.run(
            [xelatex_command, *compile_flags, tex_file.name],
            cwd=slides_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
        )
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(proc.stdout)
            handle.write(proc.stderr)
        if proc.returncode != 0:
            raise RuntimeError(f"XeLaTeX failed. See {log_path}")

    pdf_file = slides_dir / miktex_config.get("output_pdf_name", "main.pdf")
    if not pdf_file.exists():
        raise RuntimeError("XeLaTeX did not produce main.pdf.")
    result["pdf_file"] = str(pdf_file.resolve())
    return result


def _render_body(job: JobContext) -> str:
    slides = job.data["slides"]
    source_images = job.data["sources"]["images"]
    frames: list[str] = []

    frames.append(
        r"\begin{frame}{Agenda}" "\n"
        r"\tableofcontents" "\n"
        r"\end{frame}" "\n"
    )

    for section in slides["sections"]:
        frames.append(
            "\\section{" + latex_escape(section["title"]) + "}\n"
            "\\begin{frame}{"
            + latex_escape(section["title"])
            + "}\n"
            "\\begin{itemize}\n"
            + "\n".join(f"  \\item {latex_escape(item)}" for item in section["bullets"])
            + "\n\\end{itemize}\n"
            "\\end{frame}\n"
        )

    if source_images:
        image_path = normalize_file_uri(Path(source_images[0]))
        frames.append(
            r"\section{Visual Overview}" "\n"
            r"\begin{frame}{Visual Overview}" "\n"
            r"\begin{center}" "\n"
            r"\includegraphics[width=0.88\linewidth,height=0.68\textheight,keepaspectratio]{"
            + image_path
            + "}\n"
            r"\end{center}" "\n"
            r"\end{frame}" "\n"
        )

    frames.append(
        r"\section{Closing}" "\n"
        r"\begin{frame}{Closing Summary}" "\n"
        r"\begin{block}{Key Takeaways}" "\n"
        + "\n".join(latex_escape(item) + r"\\" for item in slides["sections"][-2]["bullets"][:2] + slides["sections"][-1]["bullets"][:2])
        + "\n"
        r"\end{block}" "\n"
        r"\vfill" "\n"
        r"\centering Questions and discussion" "\n"
        r"\end{frame}" "\n"
    )

    return "".join(frames)
