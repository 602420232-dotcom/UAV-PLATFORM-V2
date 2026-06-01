"""
Auto-generate unit test files
Based on pytest framework
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import ast

class PythonFunctionExtractor(ast.NodeVisitor):
    """Python AST visitor, extract function info"""
    
    def __init__(self):
        self.functions = []
        self.current_class = None
        
    def visit_ClassDef(self, node):
        """Detect class definition"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node):
        """Detect function definition"""
        # Skip private and test functions
        if node.name.startswith('_') or node.name.startswith('test_'):
            return
            
        func_info = {
            'name': node.name,
            'class': self.current_class,
            'args': [arg.arg for arg in node.args.args],
            'decorators': [d.id if hasattr(d, 'id') else str(d) for d in node.decorator_list],
            'returns': 'Any',
            'has_docstring': ast.get_docstring(node) is not None
        }
        
        self.functions.append(func_info)

def extract_functions_from_file(file_path: str) -> List[Dict]:
    """Extract function info from Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        extractor = PythonFunctionExtractor()
        extractor.visit(tree)
        
        return extractor.functions
        
    except Exception as e:
        return []

def generate_test_file(python_file: str, functions: List[Dict]) -> Tuple[bool, str]:
    """Generate unit test for Python file"""
    
    # Convert file path to test path
    path = Path(python_file)
    parts = path.parts
    
    # Find src directory
    try:
        src_idx = next(i for i, p in enumerate(parts) if p in ['src', 'algorithm_core', 'platform-core'])
        base_name = path.stem
        test_file = path.parent / f'test_{base_name}.py'
        
        # Skip if test file exists
        if test_file.exists():
            return False, "Test file already exists"
            
        # Generate test code
        test_code = generate_test_code(python_file, functions)
        
        # Write file
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)
            
        return True, str(test_file)
        
    except StopIteration:
        return False, "Cannot determine test directory"

def generate_test_code(source_file: str, functions: List[Dict]) -> str:
    """Generate test code"""
    
    module_name = Path(source_file).stem.replace('\\', '.').replace('/', '.')
    
    lines = [
        '"""',
        'Auto-generated unit test',
        f'Source: {source_file}',
        f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        '"""',
        "",
        "import pytest",
        f"from {module_name} import *",
        "",
        "",
        "class TestBasic:",
        '    """Basic test class"""',
        "",
        "    def test_import(self):",
        '        """Test module import"""',
        "        assert True",
        "",
    ]
    
    # Generate test for each function
    for func in functions:
        if func['class']:
            class_name = f"Test{func['class']}"
            lines.append("")
            lines.append(f"class {class_name}:")
            class_doc = f'Test class: {func["class"]}'
            lines.append(f'    """{class_doc}"""')
            lines.append("")
            
            # Fixture
            lines.append("    @pytest.fixture")
            lines.append(f"    def {func['class'].lower()}_instance(self):")
            fixture_doc = f'Create instance for {func["class"]}'
            lines.append(f'    """{fixture_doc}"""')
            lines.append("        # TODO: Replace with actual initialization code")
            lines.append("        return None")
            lines.append("")
            
            # Method test
            func_name = f"test_{func['name']}"
            lines.append(f"    def {func_name}(self):")
            method_doc = f'Test method: {func["name"]}'
            lines.append(f'    """{method_doc}"""')
            
            # Docstring check removed - func['has_docstring'] is bool, not string
                
            lines.append("        # TODO: Implement test logic")
            
            if func['args']:
                lines.append(f"        # Args: {', '.join(func['args'])}")
                
            lines.append("        assert True  # TODO: Replace with actual assertion")
    
    # Edge cases
    lines.extend([
        "",
        "",
        "class TestEdgeCases:",
        '    """Edge case tests"""',
        "",
        "    def test_none_input(self):",
        '        """Test None input"""',
        "        # TODO: Implement None input test",
        "        assert True",
        "",
        "    def test_empty_input(self):",
        '        """Test empty input"""',
        "        # TODO: Implement empty input test",
        "        assert True",
        "",
        "    def test_large_input(self):",
        '        """Test large data input"""',
        "        # TODO: Implement large data test",
        "        assert True",
        "",
        "    def test_invalid_input(self):",
        '        """Test invalid input"""',
        "        # TODO: Implement invalid input test",
        "        assert True",
        "",
    ])
    
    # Pytest config
    lines.extend([
        "",
        "",
        "# pytest configuration",
        "# =====================",
        "#",
        "# Run all tests:",
        "#   pytest test_*.py -v",
        "#",
        "# Run specific test:",
        "#   pytest test_*.py::TestClass::test_method -v",
        "#",
        "# Generate coverage:",
        "#   pytest test_*.py --cov=. --cov-report=html",
        "#",
        "# Markers:",
        "#   @pytest.mark.slow - slow tests",
        "#   @pytest.mark.integration - integration tests",
        "#   @pytest.mark.unit - unit tests",
        "",
    ])
    
    return '\n'.join(lines)

def scan_and_generate_tests(root_dir: str) -> Dict[str, any]:
    """Scan and generate tests"""
    
    print("=" * 60)
    print("Unit Test Auto-Generation Tool")
    print("=" * 60)
    
    # Scan Python files
    python_files = []
    exclude_dirs = {'__pycache__', '.git', '.idea', 'venv', 'env', 'node_modules', 'test', 'tests', 'example', 'examples'}
    
    for root, dirs, files in os.walk(root_dir):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py') and not file.startswith('test_'):
                python_files.append(os.path.join(root, file))
    
    print(f"\nScanning: {root_dir}")
    print(f"Found {len(python_files)} Python files\n")
    
    # Generate tests
    generated = []
    skipped = []
    
    for i, py_file in enumerate(python_files, 1):
        if i % 20 == 0:
            print(f"Progress: {i}/{len(python_files)}...")
            
        functions = extract_functions_from_file(py_file)
        
        if functions:
            success, result = generate_test_file(py_file, functions)
            
            if success:
                generated.append({
                    'file': py_file,
                    'test_file': result,
                    'functions': len(functions)
                })
            else:
                skipped.append({
                    'file': py_file,
                    'reason': result
                })
    
    # Generate report
    print(f"\nGeneration complete!")
    print(f"Generated test files: {len(generated)}")
    print(f"Skipped files: {len(skipped)}")
    
    # Save report
    report_file = os.path.join(root_dir, 'test_generation_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("Unit Test Auto-Generation Report\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Scanned: {root_dir}\n\n")
        
        f.write("Generated test files:\n")
        f.write("-" * 60 + "\n")
        
        for item in generated:
            f.write(f"\nSource: {item['file']}\n")
            f.write(f"Test: {item['test_file']}\n")
            f.write(f"Functions: {item['functions']}\n")
        
        if skipped:
            f.write("\n\nSkipped files:\n")
            f.write("-" * 60 + "\n")
            for item in skipped:
                f.write(f"\nFile: {item['file']}\n")
                f.write(f"Reason: {item['reason']}\n")
        
        f.write("\n\nNext steps:\n")
        f.write("-" * 60 + "\n")
        f.write("1. Review generated test files\n")
        f.write("2. Complete TODO sections\n")
        f.write("3. Run: pytest -v\n")
        f.write("4. Coverage: pytest --cov=. --cov-report=html\n")
    
    print(f"\nReport: {report_file}")
    
    # Show examples
    if generated:
        print("\nExamples (first 5):")
        for item in generated[:5]:
            print(f"\nGenerated: {item['test_file']}")
            print(f"  Contains: {item['functions']} test functions")
    
    print("\n" + "=" * 60)
    print("Note: Please complete TODO sections manually")
    print("=" * 60)
    
    return {
        'generated': generated,
        'skipped': skipped,
        'report': report_file
    }

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = r"d:\Developer\workplace\py\iteam\trae\data-assimilation-platform"
        
    scan_and_generate_tests(root_dir)
