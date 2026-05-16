from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    path: str
    extensions: list[str] | None = None
    max_files: int = Field(default=500, ge=1, le=5000)


class SymbolResponse(BaseModel):
    name: str
    kind: Literal["function", "class"]
    line: int
    methods: list[str] = []


class FileSummary(BaseModel):
    path: str
    language: str
    line_count: int
    function_count: int
    class_count: int
    symbols: list[SymbolResponse]
    imports: list[str]


class AnalyzeResponse(BaseModel):
    root: str
    total_files: int
    total_symbols: int
    total_lines: int
    file_summaries: list[FileSummary]


class SymbolsResponse(BaseModel):
    file: str
    language: str
    symbols: list[SymbolResponse]


class RiskResponse(BaseModel):
    risk_type: str
    severity: Literal["low", "medium", "high"]
    file: str
    description: str
    detail: dict[str, Any] = {}


class RisksResponse(BaseModel):
    root: str
    risk_count: int
    risks: list[RiskResponse]


class DocsRequest(BaseModel):
    path: str
    title: str = ""


class DocsResponse(BaseModel):
    title: str
    markdown: str
