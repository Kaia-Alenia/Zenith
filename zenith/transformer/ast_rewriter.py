import ast
from typing import List, Set

class LazyASTTransformer(ast.NodeTransformer):
    def __init__(self) -> None:
        self.modulos_detectados: Set[str] = set()

    def visit_Import(self, node: ast.Import) -> ast.Import:
        for alias in node.names:
            self.modulos_detectados.add(alias.name)
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        if node.module:
            self.modulos_detectados.add(node.module)
            for alias in node.names:
                self.modulos_detectados.add(f"{node.module}.{alias.name}")
        return node


def analizar_archivo(filepath: str) -> List[str]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            contenido = f.read()
        
        tree = ast.parse(contenido)
        transformer = LazyASTTransformer()
        transformer.visit(tree)
        return sorted(list(transformer.modulos_detectados))
    except Exception:
        return []
