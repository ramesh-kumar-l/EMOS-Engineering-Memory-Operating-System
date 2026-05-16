from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..core.exceptions import RepoInvalidPathError, RepoPathNotFoundError
from .analyzer import RepoAnalysis, analyze_repo, detect_risks
from .parser import DEFAULT_EXTENSIONS, parse_file
from .schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    DocsRequest,
    DocsResponse,
    FileSummary,
    RiskResponse,
    RisksResponse,
    SymbolResponse,
    SymbolsResponse,
)


class RepoIntelService:

    def analyze(self, req: AnalyzeRequest) -> AnalyzeResponse:
        root = self._validate_dir(req.path)
        exts = frozenset(req.extensions) if req.extensions else DEFAULT_EXTENSIONS
        analysis = analyze_repo(root, extensions=exts, max_files=req.max_files)
        return AnalyzeResponse(
            root=analysis.root,
            total_files=analysis.total_files,
            total_symbols=analysis.total_symbols,
            total_lines=analysis.total_lines,
            file_summaries=[_to_summary(fa) for fa in analysis.files],
        )

    def symbols(self, file_path: str) -> SymbolsResponse:
        p = Path(file_path)
        if not p.exists():
            raise RepoPathNotFoundError(f"File not found: {file_path}")
        if not p.is_file():
            raise RepoInvalidPathError(f"Path is not a file: {file_path}")
        fa = parse_file(p)
        if fa is None:
            raise RepoInvalidPathError(f"Unsupported file type: {p.suffix!r}")
        return SymbolsResponse(
            file=str(p),
            language=fa.language,
            symbols=[_to_sym(s) for s in fa.symbols],
        )

    def risks(self, req: AnalyzeRequest) -> RisksResponse:
        root = self._validate_dir(req.path)
        exts = frozenset(req.extensions) if req.extensions else DEFAULT_EXTENSIONS
        analysis = analyze_repo(root, extensions=exts, max_files=req.max_files)
        risk_list = detect_risks(analysis)
        return RisksResponse(
            root=analysis.root,
            risk_count=len(risk_list),
            risks=[
                RiskResponse(
                    risk_type=r.risk_type,
                    severity=r.severity,
                    file=r.file,
                    description=r.description,
                    detail=r.detail,
                )
                for r in risk_list
            ],
        )

    def generate_docs(self, req: DocsRequest) -> DocsResponse:
        root = self._validate_dir(req.path)
        analysis = analyze_repo(root, max_files=500)
        title = req.title or root.name
        return DocsResponse(title=title, markdown=_render_markdown(title, analysis))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _validate_dir(self, path_str: str) -> Path:
        p = Path(path_str)
        if not p.exists():
            raise RepoPathNotFoundError(f"Path does not exist: {path_str}")
        if not p.is_dir():
            raise RepoInvalidPathError(f"Path is not a directory: {path_str}")
        return p


def _to_sym(s) -> SymbolResponse:
    return SymbolResponse(name=s.name, kind=s.kind, line=s.line, methods=s.methods)


def _to_summary(fa) -> FileSummary:
    funcs = [s for s in fa.symbols if s.kind == "function"]
    classes = [s for s in fa.symbols if s.kind == "class"]
    return FileSummary(
        path=fa.path,
        language=fa.language,
        line_count=fa.line_count,
        function_count=len(funcs),
        class_count=len(classes),
        symbols=[_to_sym(s) for s in fa.symbols],
        imports=fa.imports,
    )


def _render_markdown(title: str, analysis: RepoAnalysis) -> str:
    lines: list[str] = [
        f"# {title}",
        "",
        f"**Root:** `{analysis.root}`",
        "",
        "## Overview",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Files | {analysis.total_files} |",
        f"| Symbols | {analysis.total_symbols} |",
        f"| Total Lines | {analysis.total_lines} |",
        "",
    ]

    lang_counts = Counter(fa.language for fa in analysis.files)
    lines += ["## Language Breakdown", ""]
    for lang, count in lang_counts.most_common():
        lines.append(f"- **{lang}**: {count} file(s)")
    lines.append("")

    lines += ["## File Index", ""]
    for fa in analysis.files:
        funcs = [s for s in fa.symbols if s.kind == "function"]
        classes = [s for s in fa.symbols if s.kind == "class"]
        lines.append(f"### `{fa.path}` ({fa.language})")
        lines.append(
            f"*{fa.line_count} lines · {len(funcs)} function(s) · {len(classes)} class(es)*"
        )
        if classes:
            lines.append("")
            lines.append("**Classes:** " + ", ".join(f"`{c.name}`" for c in classes))
        if funcs:
            lines.append("")
            lines.append("**Functions:** " + ", ".join(f"`{f.name}`" for f in funcs))
        if fa.imports:
            preview = ", ".join(f"`{i}`" for i in fa.imports[:10])
            suffix = f" *(+{len(fa.imports) - 10} more)*" if len(fa.imports) > 10 else ""
            lines.append("")
            lines.append(f"**Imports:** {preview}{suffix}")
        lines.append("")

    return "\n".join(lines)
