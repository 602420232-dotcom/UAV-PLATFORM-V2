"""
Type Annotations Generator for Python Files
Automatically add type annotations to key functions
"""

import os
import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# Type annotation patterns
TYPE_MAPPING = {
    'id': 'str',
    'name': 'str',
    'data': 'Dict[str, Any]',
    'config': 'Dict[str, Any]',
    'params': 'Dict[str, Any]',
    'options': 'Dict[str, Any]',
    'result': 'Any',
    'response': 'Dict[str, Any]',
    'error': 'Exception',
    'message': 'str',
    'value': 'Any',
    'count': 'int',
    'size': 'int',
    'limit': 'int',
    'page': 'int',
    'enabled': 'bool',
    'active': 'bool',
    'timestamp': 'float',
    'duration': 'int',
    'callback': 'Callable',
    'executor': 'ExecutorService',
    'task': 'Callable',
    'file': 'str',
    'path': 'str',
    'url': 'str',
    'key': 'str',
    'token': 'str',
    'email': 'str',
    'password': 'str',
    'host': 'str',
    'port': 'int',
    'username': 'str',
    'status': 'str',
    'type': 'str',
    'mode': 'str',
    'level': 'str',
    'output': 'Any',
    'input': 'Any',
    'source': 'str',
    'target': 'str',
}

def infer_type(arg_name: str) -> str:
    """Infer type from argument name"""
    # Check exact match
    if arg_name in TYPE_MAPPING:
        return TYPE_MAPPING[arg_name]
    
    # Check patterns
    if 'id' in arg_name.lower():
        return 'str'
    if 'count' in arg_name.lower() or 'size' in arg_name.lower():
        return 'int'
    if 'flag' in arg_name.lower() or 'enabled' in arg_name.lower():
        return 'bool'
    if 'timestamp' in arg_name.lower() or 'time' in arg_name.lower():
        return 'float'
    if 'name' in arg_name.lower() or 'message' in arg_name.lower():
        return 'str'
    
    return 'Any'

def add_annotations_to_file(file_path: str) -> Dict:
    """Add type annotations to a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        original_lines = lines.copy()
        changes_made = []
        
        # Check if already has typing imports
        has_typing_import = any('from typing import' in line for line in lines)
        
        # Find functions without type annotations
        for i, line in enumerate(lines):
            # Match function definition
            match = re.match(r'^(\s*)def (\w+)\((.*)\):', line)
            if match:
                indent, func_name, args_str = match.groups()
                
                # Skip private functions
                if func_name.startswith('_'):
                    continue
                
                # Parse arguments
                args = [arg.strip().split(':')[0].strip() for arg in args_str.split(',') if arg.strip()]
                
                # Skip if no arguments or too many
                if not args or len(args) > 5:
                    continue
                
                # Check if already has annotations
                if ':' in args_str:
                    continue
                
                # Infer types
                arg_types = [infer_type(arg) for arg in args]
                
                # Check if any type is not 'Any'
                if all(t == 'Any' for t in arg_types):
                    continue
                
                # Create annotated arguments
                annotated_args = ', '.join([f'{arg}: {arg_type}' for arg, arg_type in zip(args, arg_types)])
                
                # Replace line
                new_line = f'{indent}def {func_name}({annotated_args}):\n'
                lines[i] = new_line
                
                changes_made.append({
                    'line': i + 1,
                    'function': func_name,
                    'args': args,
                    'types': arg_types
                })
        
        # Add typing imports if needed
        if changes_made and not has_typing_import:
            # Find where to insert import
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith('#'):
                    insert_idx = i
                    break
            
            # Insert imports
            imports = [
                f'# Type annotations added: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n',
                'from typing import Dict, List, Any, Optional, Callable, Tuple\n',
                '\n'
            ]
            
            lines = lines[:insert_idx] + imports + lines[insert_idx:]
        
        # Write back if changed
        if lines != original_lines:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return {
                'file': file_path,
                'changes': len(changes_made),
                'status': 'SUCCESS',
                'details': changes_made
            }
        
        return {
            'file': file_path,
            'changes': 0,
            'status': 'NO_CHANGES'
        }
        
    except Exception as e:
        return {
            'file': file_path,
            'error': str(e),
            'status': 'ERROR'
        }

def find_python_files(root_dir: str) -> List[str]:
    """Find all Python files"""
    python_files = []
    exclude_dirs = {'__pycache__', '.git', '.idea', 'venv', 'env', 'node_modules'}
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py') and not file.startswith('test_'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def main():
    """Main function"""
    print("=" * 60)
    print("Type Annotations Generator")
    print("=" * 60)
    
    # Find Python files
    root_dir = r"d:\Developer\workplace\py\iteam\trae\data-assimilation-platform"
    python_files = find_python_files(root_dir)
    
    print(f"\nFound {len(python_files)} Python files\n")
    
    # Add type annotations
    results = []
    for i, py_file in enumerate(python_files, 1):
        if i % 20 == 0:
            print(f"Progress: {i}/{len(python_files)}...")
        
        result = add_annotations_to_file(py_file)
        results.append(result)
    
    # Generate report
    success = sum(1 for r in results if r['status'] == 'SUCCESS')
    no_changes = sum(1 for r in results if r['status'] == 'NO_CHANGES')
    errors = sum(1 for r in results if r['status'] == 'ERROR')
    total_changes = sum(r['changes'] for r in results if r['status'] == 'SUCCESS')
    
    print(f"\nGeneration complete!")
    print(f"Files modified: {success}")
    print(f"Files no changes: {no_changes}")
    print(f"Files with errors: {errors}")
    print(f"Total annotations added: {total_changes}")
    
    # Save report
    report_file = os.path.join(root_dir, 'type_annotations_added.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("Type Annotations Added Report\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total files: {len(python_files)}\n")
        f.write(f"Files modified: {success}\n")
        f.write(f"Annotations added: {total_changes}\n\n")
        
        f.write("Modified files:\n")
        f.write("-" * 60 + "\n")
        
        for result in results:
            if result['status'] == 'SUCCESS':
                f.write(f"\n{result['file']}\n")
                f.write(f"  Annotations added: {result['changes']}\n")
                for detail in result['details'][:3]:  # Show first 3
                    f.write(f"  - {detail['function']}({', '.join(detail['args'])})\n")
    
    print(f"\nReport: {report_file}")
    print("\n" + "=" * 60)
    print("Note: Review changes and run tests to verify")
    print("=" * 60)

if __name__ == '__main__':
    main()
