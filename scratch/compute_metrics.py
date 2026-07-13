import os
import ast
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/Dev Suri/.gemini/antigravity/scratch/prd_generator")

def get_cyclomatic_complexity(node):
    """Calculates cyclomatic complexity using AST."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.AsyncWith, ast.IfExp, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity

def main():
    py_files = []
    total_raw_lines = 0
    total_code_lines = 0
    
    agent_count = 0
    test_files_count = 0
    test_cases_count = 0
    
    functions = []
    files_info = []
    
    # Walk directory
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Exclude virtual environment and git folders
        if any(p in Path(root).parts for p in (".venv", ".git", "__pycache__", "build", "dist")):
            continue
            
        for file in files:
            if file.endswith(".py"):
                full_path = Path(root) / file
                py_files.append(full_path)
                
                # Check if it is a test file
                is_test = file.startswith("test_") or "test" in root.lower() or "test" in file.lower()
                if file.startswith("test_"):
                    test_files_count += 1
                
                # Read content
                try:
                    content = full_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    try:
                        content = full_path.read_text(encoding="cp1252")
                    except Exception:
                        continue
                
                lines = content.splitlines()
                raw_lines = len(lines)
                total_raw_lines += raw_lines
                
                # Code lines (strip empty and comments)
                code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))
                total_code_lines += code_lines
                
                files_info.append({
                    "path": full_path.relative_to(PROJECT_ROOT),
                    "raw_lines": raw_lines,
                    "code_lines": code_lines,
                    "size": full_path.stat().st_size
                })
                
                # Parse AST
                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue
                    
                # Look for agents
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Simple heuristic for agents (ends with Agent or inherits from BaseAgent/BaseDocumentAgent)
                        is_agent_class = node.name.endswith("Agent")
                        for base in node.bases:
                            if isinstance(base, ast.Name) and base.id in ("BaseAgent", "BaseDocumentAgent", "BaseAgent"):
                                is_agent_class = True
                        if is_agent_class:
                            agent_count += 1
                            
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Function info
                        # Check if function is in a test file and starts with test_
                        if is_test and node.name.startswith("test_"):
                            test_cases_count += 1
                            
                        # Calculate line length
                        if hasattr(node, "end_lineno") and node.end_lineno is not None:
                            length = node.end_lineno - node.lineno + 1
                        else:
                            length = 1
                            
                        complexity = get_cyclomatic_complexity(node)
                        functions.append({
                            "name": node.name,
                            "file": full_path.relative_to(PROJECT_ROOT),
                            "length": length,
                            "complexity": complexity,
                            "line": node.lineno
                        })

    # Sort files and functions
    files_info.sort(key=lambda x: x["raw_lines"], reverse=True)
    functions.sort(key=lambda x: x["length"], reverse=True)
    
    avg_func_len = sum(f["length"] for f in functions) / len(functions) if functions else 0
    largest_file = files_info[0] if files_info else None
    largest_func = functions[0] if functions else None
    
    # Sort functions by complexity to find the most complex
    functions.sort(key=lambda x: x["complexity"], reverse=True)
    highest_complexity_func = functions[0] if functions else None
    
    print("--- METRICS REPORT ---")
    print(f"Total Python Files: {len(py_files)}")
    print(f"Total Raw Lines: {total_raw_lines}")
    print(f"Total Code Lines: {total_code_lines}")
    print(f"Number of Agents: {agent_count}")
    print(f"Number of Test Files: {test_files_count}")
    print(f"Number of Test Cases: {test_cases_count}")
    print(f"Average Function Length: {avg_func_len:.2f} lines")
    if largest_file:
        print(f"Largest File: {largest_file['path']} ({largest_file['raw_lines']} lines, {largest_file['size']} bytes)")
    if largest_func:
        # Re-sort functions by length to print largest function
        functions.sort(key=lambda x: x["length"], reverse=True)
        largest_func = functions[0]
        print(f"Largest Function: {largest_func['name']} in {largest_func['file']} ({largest_func['length']} lines, starts at line {largest_func['line']})")
    if highest_complexity_func:
        print(f"Highest Cyclomatic Complexity: {highest_complexity_func['name']} in {highest_complexity_func['file']} (Complexity: {highest_complexity_func['complexity']}, starts at line {highest_complexity_func['line']})")

if __name__ == "__main__":
    main()
