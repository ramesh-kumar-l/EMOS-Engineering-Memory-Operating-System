"""Repo structure analyzer: directory walk, coupling metrics, risk detection."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .parser import DEFAULT_EXTENSIONS, FileAnalysis, _SKIP_DIRS, parse_file

RiskSeverity = Literal["low", "medium", "high"]
RiskType = Literal["high_fan_out", "high_fan_in", "circular_dependency"]

# Thresholds
_FAN_OUT_MEDIUM = 10
_FAN_OUT_HIGH = 20
_FAN_IN_MEDIUM = 8
_FAN_IN_HIGH = 15


@dataclass
class CouplingRisk:
    risk_type: RiskType
    severity: RiskSeverity
    file: str
    description: str
    detail: dict = field(default_factory=dict)


@dataclass
class RepoAnalysis:
    root: str
    total_files: int
    total_symbols: int
    total_lines: int
    files: list[FileAnalysis]


def analyze_repo(
    root: Path,
    extensions: frozenset[str] | None = None,
    max_files: int = 500,
) -> RepoAnalysis:
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS

    files: list[FileAnalysis] = []

    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in extensions:
            continue
        # Skip non-project directories
        if _SKIP_DIRS & set(p.parts):
            continue

        fa = parse_file(p)
        if fa is None:
            continue

        try:
            fa.path = str(p.relative_to(root))
        except ValueError:
            pass  # absolute path if outside root (shouldn't happen)

        files.append(fa)
        if len(files) >= max_files:
            break

    return RepoAnalysis(
        root=str(root),
        total_files=len(files),
        total_symbols=sum(len(f.symbols) for f in files),
        total_lines=sum(f.line_count for f in files),
        files=files,
    )


def detect_risks(analysis: RepoAnalysis) -> list[CouplingRisk]:
    risks: list[CouplingRisk] = []

    # Map: stem → relative path (for internal module resolution)
    stem_to_path: dict[str, str] = {
        Path(fa.path).stem: fa.path for fa in analysis.files
    }

    # Map: file → list of files that import it (fan-in)
    referenced_by: dict[str, list[str]] = defaultdict(list)

    for fa in analysis.files:
        n = len(fa.imports)
        # Fan-out
        if n >= _FAN_OUT_HIGH:
            severity: RiskSeverity = "high"
        elif n >= _FAN_OUT_MEDIUM:
            severity = "medium"
        else:
            severity = "low"

        if severity != "low":
            risks.append(CouplingRisk(
                risk_type="high_fan_out",
                severity=severity,
                file=fa.path,
                description=(
                    f"Imports {n} modules — may indicate excessive coupling or a utility dump"
                ),
                detail={"import_count": n, "imports": fa.imports},
            ))

        # Accumulate fan-in data
        for imp in fa.imports:
            if imp in stem_to_path and stem_to_path[imp] != fa.path:
                referenced_by[stem_to_path[imp]].append(fa.path)

    # Fan-in risks
    for fa in analysis.files:
        refs = referenced_by.get(fa.path, [])
        n = len(refs)
        if n >= _FAN_IN_HIGH:
            severity = "high"
        elif n >= _FAN_IN_MEDIUM:
            severity = "medium"
        else:
            continue
        risks.append(CouplingRisk(
            risk_type="high_fan_in",
            severity=severity,
            file=fa.path,
            description=(
                f"Imported by {n} other files — critical shared module, "
                "changes carry high blast radius"
            ),
            detail={"referenced_by_count": n, "referenced_by": refs[:10]},
        ))

    # Circular dependency detection (DFS over internal imports)
    adjacency: dict[str, list[str]] = {}
    for fa in analysis.files:
        neighbors = [
            stem_to_path[imp]
            for imp in fa.imports
            if imp in stem_to_path and stem_to_path[imp] != fa.path
        ]
        adjacency[fa.path] = neighbors

    for cycle in _find_cycles(adjacency):
        risks.append(CouplingRisk(
            risk_type="circular_dependency",
            severity="high",
            file=cycle[0],
            description="Circular dependency: " + " → ".join(cycle),
            detail={"cycle": cycle},
        ))

    return risks


def _find_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """DFS-based cycle detection. Returns each cycle as a list of nodes (start repeated at end)."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {n: WHITE for n in graph}
    seen_cycles: set[frozenset] = set()
    cycles: list[list[str]] = []

    def dfs(node: str, stack: list[str]) -> None:
        color[node] = GRAY
        stack.append(node)
        for neighbor in graph.get(node, []):
            if color.get(neighbor, BLACK) == GRAY:
                idx = stack.index(neighbor)
                cycle = stack[idx:] + [neighbor]
                key = frozenset(cycle)
                if key not in seen_cycles:
                    seen_cycles.add(key)
                    cycles.append(cycle)
            elif color.get(neighbor, BLACK) == WHITE:
                dfs(neighbor, stack)
        stack.pop()
        color[node] = BLACK

    for node in list(graph.keys()):
        if color[node] == WHITE:
            dfs(node, [])

    return cycles
