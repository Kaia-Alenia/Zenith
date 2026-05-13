import ast

class LazyASTTransformer(ast.NodeTransformer):
    def __init__(self) -> None:
        self.detected_modules: set[str] = set()

    def visit_Import(self, node: ast.Import) -> ast.Import:
        for alias in node.names:
            self.detected_modules.add(alias.name)
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        if node.module:
            self.detected_modules.add(node.module)
            for alias in node.names:
                self.detected_modules.add(f"{node.module}.{alias.name}")
        return node


def analyze_file(filepath: str) -> list[str]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        tree = ast.parse(content)
        transformer = LazyASTTransformer()
        transformer.visit(tree)
        return sorted(list(transformer.detected_modules))
    except Exception:
        return []
