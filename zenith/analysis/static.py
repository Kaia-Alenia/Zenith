import ast
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class StaticImport:
    module: str
    alias: Optional[str]
    is_nested: bool
    line_number: int
    is_dynamic_call: bool
    context: Optional[str] = None
    
@dataclass
class StaticAnalysisResult:
    filepath: str
    imports: List[StaticImport]

class ImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports: List[StaticImport] = []
        self._current_scope = 0
        self._in_type_checking = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._current_scope += 1
        self.generic_visit(node)
        self._current_scope -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._current_scope += 1
        self.generic_visit(node)
        self._current_scope -= 1

    def visit_ClassDef(self, node: ast.ClassDef):
        self._current_scope += 1
        self.generic_visit(node)
        self._current_scope -= 1
        
    def visit_If(self, node: ast.If):
        # Check if this is `if TYPE_CHECKING:` or `if typing.TYPE_CHECKING:`
        was_type_checking = self._in_type_checking
        is_type_checking = False
        
        if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            is_type_checking = True
        elif isinstance(node.test, ast.Attribute) and node.test.attr == "TYPE_CHECKING":
            is_type_checking = True
            
        if is_type_checking:
            self._in_type_checking = True
            
        self._current_scope += 1
        self.generic_visit(node)
        self._current_scope -= 1
        
        if is_type_checking:
            self._in_type_checking = was_type_checking

    def visit_Import(self, node: ast.Import):
        is_nested = self._current_scope > 0
        ctx = "TYPE_CHECKING" if self._in_type_checking else None
        
        for alias in node.names:
            self.imports.append(StaticImport(
                module=alias.name,
                alias=alias.asname,
                is_nested=is_nested,
                line_number=node.lineno,
                is_dynamic_call=False,
                context=ctx
            ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        is_nested = self._current_scope > 0
        ctx = "TYPE_CHECKING" if self._in_type_checking else None
        
        module = node.module or ""
        # Handle relative imports if level > 0? For now just use module name
        if node.level > 0:
            module = "." * node.level + module

        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module and alias.name != "*" else module
            
            self.imports.append(StaticImport(
                module=full_name,
                alias=alias.asname,
                is_nested=is_nested,
                line_number=node.lineno,
                is_dynamic_call=False,
                context=ctx
            ))
        self.generic_visit(node)
        
    def visit_Call(self, node: ast.Call):
        # Detect dynamic imports like importlib.import_module() or __import__()
        is_nested = self._current_scope > 0
        ctx = "TYPE_CHECKING" if self._in_type_checking else None
        
        if isinstance(node.func, ast.Name) and node.func.id == "__import__":
            self.imports.append(StaticImport(
                module="<dynamic>",
                alias=None,
                is_nested=is_nested,
                line_number=node.lineno,
                is_dynamic_call=True,
                context=ctx
            ))
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "importlib":
                self.imports.append(StaticImport(
                    module="<dynamic>",
                    alias=None,
                    is_nested=is_nested,
                    line_number=node.lineno,
                    is_dynamic_call=True,
                    context=ctx
                ))
                
        self.generic_visit(node)

def analyze_file(filepath: str) -> StaticAnalysisResult:
    try:
        content = Path(filepath).read_text(encoding="utf-8")
        tree = ast.parse(content, filename=filepath)
        visitor = ImportVisitor()
        visitor.visit(tree)
        return StaticAnalysisResult(filepath=filepath, imports=visitor.imports)
    except Exception:
        return StaticAnalysisResult(filepath=filepath, imports=[])
