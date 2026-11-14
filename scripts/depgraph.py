"""Build a module dependency graph for src/ by reading import statements."""
import ast
from pathlib import Path

SRC = Path("src")


def module_name(path):
    return path.stem


def build_graph(src_dir=SRC):
    """Return {module: set(modules it imports from src)}."""
    graph = {}
    for f in sorted(Path(src_dir).glob("*.py")):
        if f.name == "__init__.py":
            continue
        deps = set()
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("src."):
                deps.add(node.module.split(".", 1)[1])
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.startswith("src."):
                        deps.add(a.name.split(".", 1)[1])
        graph[module_name(f)] = deps
    return graph


def reverse_graph(graph):
    rev = {m: set() for m in graph}
    for m, deps in graph.items():
        for d in deps:
            rev.setdefault(d, set()).add(m)
    return rev


def transitive(start, graph):
    seen, stack = set(), [start]
    while stack:
        cur = stack.pop()
        for nxt in graph.get(cur, ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen
