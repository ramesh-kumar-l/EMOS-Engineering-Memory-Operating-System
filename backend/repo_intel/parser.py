"""Tree-sitter-based code parser for Python and JS/TS files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import tree_sitter_javascript as tsjs
import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser

_PY_LANG = Language(tspython.language())
_JS_LANG = Language(tsjs.language())

_PY_PARSER = Parser(_PY_LANG)
_JS_PARSER = Parser(_JS_LANG)

LanguageID = Literal["python", "javascript", "unknown"]

EXTENSION_MAP: dict[str, LanguageID] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "javascript",
    ".jsx": "javascript",
    ".tsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
}

DEFAULT_EXTENSIONS: frozenset[str] = frozenset(EXTENSION_MAP.keys())

# Directories always skipped during repo walks
_SKIP_DIRS: frozenset[str] = frozenset({
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".tox", "dist", "build", ".mypy_cache", ".pytest_cache",
})


@dataclass
class Symbol:
    name: str
    kind: Literal["function", "class"]
    line: int
    methods: list[str] = field(default_factory=list)


@dataclass
class FileAnalysis:
    path: str
    language: LanguageID
    line_count: int
    symbols: list[Symbol]
    imports: list[str]


def detect_language(path: Path) -> LanguageID:
    return EXTENSION_MAP.get(path.suffix.lower(), "unknown")


def _text(node: Node) -> str:
    return node.text.decode("utf-8", errors="replace") if node.text else ""


# ── Python extractor ──────────────────────────────────────────────────────────

def _extract_python(source: bytes) -> tuple[list[Symbol], list[str]]:
    tree = _PY_PARSER.parse(source)
    symbols: list[Symbol] = []
    imports: list[str] = []

    def _walk(node: Node, parent_class: str | None = None) -> None:
        if node.type == "import_statement":
            # children_by_field_name handles: import os; import os, sys; import os as o
            for name_node in node.children_by_field_name("name"):
                if name_node.type == "aliased_import":
                    mod = name_node.child_by_field_name("name")
                    if mod:
                        imports.append(_text(mod).split(".")[0])
                else:
                    raw = _text(name_node).split(".")[0]
                    if raw:
                        imports.append(raw)

        elif node.type == "import_from_statement":
            mod = node.child_by_field_name("module_name")
            if mod:
                raw = _text(mod).lstrip(".")  # strip relative-import dots
                if raw:
                    imports.append(raw.split(".")[0])

        elif node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                fname = _text(name_node)
                if parent_class:
                    for sym in symbols:
                        if sym.name == parent_class and sym.kind == "class":
                            sym.methods.append(fname)
                            break
                else:
                    symbols.append(Symbol(name=fname, kind="function", line=node.start_point[0] + 1))
            return  # don't recurse into function body

        elif node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                cname = _text(name_node)
                sym = Symbol(name=cname, kind="class", line=node.start_point[0] + 1)
                symbols.append(sym)
                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        _walk(child, parent_class=cname)
            return  # body already walked above

        for child in node.children:
            _walk(child, parent_class)

    _walk(tree.root_node)
    return symbols, imports


# ── JavaScript / TypeScript extractor ────────────────────────────────────────

def _strip_quotes(raw: str) -> str:
    return raw.strip("'\"` \t")


def _module_name(raw: str) -> str:
    raw = _strip_quotes(raw)
    if not raw:
        return ""
    if raw.startswith("."):
        return raw  # relative import — keep path
    if raw.startswith("@"):
        parts = raw.split("/")
        return "/".join(parts[:2]) if len(parts) >= 2 else raw
    return raw.split("/")[0]


def _extract_javascript(source: bytes) -> tuple[list[Symbol], list[str]]:
    tree = _JS_PARSER.parse(source)
    symbols: list[Symbol] = []
    imports: list[str] = []

    def _walk(node: Node, parent_class: str | None = None) -> None:
        if node.type == "import_statement":
            src = node.child_by_field_name("source")
            if src:
                name = _module_name(_text(src))
                if name:
                    imports.append(name)

        elif node.type == "call_expression":
            func = node.child_by_field_name("function")
            args = node.child_by_field_name("arguments")
            if func and _text(func) == "require" and args:
                for arg in args.named_children:
                    if arg.type in ("string", "template_string"):
                        name = _module_name(_text(arg))
                        if name:
                            imports.append(name)

        elif node.type == "function_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                fname = _text(name_node)
                if parent_class:
                    for sym in symbols:
                        if sym.name == parent_class and sym.kind == "class":
                            sym.methods.append(fname)
                            break
                else:
                    symbols.append(Symbol(name=fname, kind="function", line=node.start_point[0] + 1))

        elif node.type == "method_definition":
            name_node = node.child_by_field_name("name")
            if name_node and parent_class:
                mname = _text(name_node)
                for sym in symbols:
                    if sym.name == parent_class and sym.kind == "class":
                        sym.methods.append(mname)
                        break
            return

        elif node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                cname = _text(name_node)
                sym = Symbol(name=cname, kind="class", line=node.start_point[0] + 1)
                symbols.append(sym)
                body = node.child_by_field_name("body")
                if body:
                    for child in body.children:
                        _walk(child, parent_class=cname)
            return

        elif node.type in ("lexical_declaration", "variable_declaration"):
            for child in node.named_children:
                if child.type == "variable_declarator":
                    vname_node = child.child_by_field_name("name")
                    value_node = child.child_by_field_name("value")
                    if vname_node and value_node:
                        vname = _text(vname_node)
                        if value_node.type in ("function", "arrow_function"):
                            symbols.append(Symbol(name=vname, kind="function", line=child.start_point[0] + 1))
                        elif value_node.type == "class":
                            sym = Symbol(name=vname, kind="class", line=child.start_point[0] + 1)
                            symbols.append(sym)
                            body = value_node.child_by_field_name("body")
                            if body:
                                for c in body.children:
                                    _walk(c, parent_class=vname)

        for child in node.children:
            _walk(child, parent_class)

    _walk(tree.root_node)
    return symbols, imports


# ── Public API ────────────────────────────────────────────────────────────────

def parse_file(path: Path) -> FileAnalysis | None:
    lang = detect_language(path)
    if lang == "unknown":
        return None
    try:
        source = path.read_bytes()
    except OSError:
        return None

    line_count = source.count(b"\n") + 1

    if lang == "python":
        symbols, raw_imports = _extract_python(source)
    else:
        symbols, raw_imports = _extract_javascript(source)

    # Deduplicate imports while preserving order
    seen: set[str] = set()
    imports: list[str] = []
    for imp in raw_imports:
        if imp not in seen:
            seen.add(imp)
            imports.append(imp)

    return FileAnalysis(
        path=str(path),
        language=lang,
        line_count=line_count,
        symbols=symbols,
        imports=imports,
    )
