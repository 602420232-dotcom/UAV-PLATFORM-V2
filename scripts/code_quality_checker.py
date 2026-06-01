"""
Code Quality Checker
Check for common code quality issues
"""

import os
import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class CodeQualityChecker:
    """Check code quality issues"""
    
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.issues = []
        self.warnings = []
        self.info = []
        
    def check_all(self):
        """Check all code files"""
        print("=" * 60)
        print("Code Quality Checker")
        print("=" * 60)
        
        # Find all code files
        code_files = self._find_code_files()
        print(f"\nFound {len(code_files)} code files\n")
        
        # Check each file
        for code_file in code_files:
            self._check_code_file(code_file)
            
        # Generate report
        self._generate_report()
        
    def _find_code_files(self) -> List[str]:
        """Find all code files"""
        code_files = []
        exclude_dirs = {'__pycache__', '.git', '.idea', 'venv', 'node_modules', 'build', 'dist', 'target'}
        
        extensions = {'.py', '.java', '.js', '.ts', '.jsx', '.tsx'}
        
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    code_files.append(os.path.join(root, file))
        
        return code_files
    
    def _check_code_file(self, code_file: str):
        """Check single code file"""
        try:
            with open(code_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Check for print statements (Python)
            if code_file.endswith('.py'):
                print_count = len(re.findall(r'\bprint\s*\(', content))
                if print_count > 5:
                    self.warnings.append({
                        'file': code_file,
                        'type': 'Too many print statements',
                        'severity': 'LOW',
                        'count': print_count
                    })
            
            # Check for TODO/FIXME comments
            todo_matches = re.findall(r'(TODO|FIXME|HACK|XXX):?\s*(.*)', content, re.IGNORECASE)
            if todo_matches:
                self.info.append({
                    'file': code_file,
                    'type': 'TODO/FIXME comments',
                    'count': len(todo_matches)
                })
            
            # Check for commented out code
            commented_code = len(re.findall(r'^\s*#.*[=\+\-\*/].*$', content, re.MULTILINE))
            if commented_code > 10:
                self.warnings.append({
                    'file': code_file,
                    'type': 'Many commented lines',
                    'severity': 'LOW',
                    'count': commented_code
                })
            
            # Check for long lines
            long_lines = 0
            for i, line in enumerate(content.split('\n'), 1):
                if len(line) > 120:
                    long_lines += 1
                    
            if long_lines > 10:
                self.warnings.append({
                    'file': code_file,
                    'type': 'Many long lines (>120 chars)',
                    'severity': 'LOW',
                    'count': long_lines
                })
                
        except Exception as e:
            pass
    
    def _generate_report(self):
        """Generate check report"""
        report_file = os.path.join(self.root_dir, 'code_quality_report.txt')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("Code Quality Check Report\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Root: {self.root_dir}\n\n")
            
            # Warnings
            f.write("WARNINGS\n")
            f.write("-" * 60 + "\n")
            
            if self.warnings:
                for i, warning in enumerate(self.warnings, 1):
                    f.write(f"\n{i}. [{warning['severity']}] {warning['type']}\n")
                    f.write(f"   File: {warning['file']}\n")
                    f.write(f"   Count: {warning.get('count', 'N/A')}\n")
            else:
                f.write("No warnings!\n")
            
            # Info
            f.write("\n\nINFO\n")
            f.write("-" * 60 + "\n")
            
            if self.info:
                for item in self.info[:20]:  # Show first 20
                    f.write(f"\n{item['file']}: {item['type']} ({item['count']})\n")
            else:
                f.write("No additional info\n")
            
            # Summary
            f.write("\n\n" + "=" * 60 + "\n")
            f.write("SUMMARY\n")
            f.write("=" * 60 + "\n")
            f.write(f"Warnings: {len(self.warnings)}\n")
            f.write(f"Info items: {len(self.info)}\n")
            
            if self.warnings:
                f.write("\nRecommendation: Review warnings and improve code quality\n")
            else:
                f.write("\n✅ Code quality looks good!\n")
        
        print(f"\nReport: {report_file}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Warnings: {len(self.warnings)}")
        print(f"Info items: {len(self.info)}")
        
        if self.warnings:
            print("\nTop warnings:")
            for warning in self.warnings[:10]:
                print(f"  - {warning['type']} ({warning['count']})")
                print(f"    {warning['file']}")
        
        print("\n" + "=" * 60)

def main():
    root_dir = r"d:\Developer\workplace\py\iteam\trae"
    checker = CodeQualityChecker(root_dir)
    checker.check_all()

if __name__ == '__main__':
    main()
