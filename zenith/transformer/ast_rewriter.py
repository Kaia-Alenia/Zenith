
import ast
import sys
from pathlib import Path
from typing import Optional

from zenith.core.constants import _STDLIB_ROOTS


class ImportCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.detected = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.detected.add(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.detected.add(node.module)
            for alias in node.names:
                if alias.name != "*":
                    self.detected.add("{}.{}".format(node.module, alias.name))


def analyze_file(filepath: str) -> list[str]:
    try:
        content = Path(filepath).read_text(encoding="utf-8")
        tree = ast.parse(content, filename=filepath)
        collector = ImportCollector()
        collector.visit(tree)
        return sorted(collector.detected)
    except Exception:
        return []


def analyze_stdlib_only(filepath: str, parsed_modules: Optional[list[str]] = None) -> list[str]:
    if parsed_modules is None:
        parsed_modules = analyze_file(filepath)
    return [m for m in parsed_modules if m.split(".")[0] in _STDLIB_ROOTS]


def analyze_third_party(filepath: str, parsed_modules: Optional[list[str]] = None) -> list[str]:
    if parsed_modules is None:
        parsed_modules = analyze_file(filepath)
    return [m for m in parsed_modules if m.split(".")[0] not in _STDLIB_ROOTS]
