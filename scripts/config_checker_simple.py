"""
Simple Configuration Files Consistency Checker
Check YAML/properties files without external dependencies
"""

import os
import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class SimpleConfigChecker:
    """Simple config file checker without yaml dependency"""
    
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.issues = []
        self.warnings = []
        self.files_checked = 0
        
    def check_all(self):
        """Check all config files"""
        print("=" * 60)
        print("Simple Configuration Checker (No Dependencies)")
        print("=" * 60)
        
        # Find all config files
        config_files = self._find_config_files()
        print(f"\nFound {len(config_files)} config files\n")
        
        # Check each file
        for config_file in config_files:
            self._check_config_file(config_file)
            
        # Generate report
        self._generate_report()
        
    def _find_config_files(self) -> List[str]:
        """Find all configuration files"""
        config_files = []
        exclude_dirs = {'__pycache__', '.git', '.idea', 'venv', 'node_modules'}
        
        extensions = ['.yml', '.yaml', '.properties', '.conf', '.config']
        
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    config_files.append(os.path.join(root, file))
        
        return config_files
    
    def _check_config_file(self, config_file: str):
        """Check single config file"""
        self.files_checked += 1
        
        try:
            with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Check for hardcoded passwords
            if re.search(r'password\s*[:=]\s*["\']?[^${\s]+', content, re.IGNORECASE):
                # Exclude environment variables
                lines_with_password = []
                for i, line in enumerate(content.split('\n'), 1):
                    if re.search(r'password\s*[:=]', line, re.IGNORECASE):
                        if not re.search(r'\$\{|ENV|SECRET', line):
                            lines_with_password.append((i, line.strip()))
                
                if lines_with_password:
                    self.issues.append({
                        'file': config_file,
                        'type': 'Hardcoded password',
                        'severity': 'HIGH',
                        'details': lines_with_password[:3]  # Show first 3
                    })
            
            # Check for debug mode
            if re.search(r'debug\s*[:=]\s*true', content, re.IGNORECASE):
                self.warnings.append({
                    'file': config_file,
                    'type': 'Debug mode enabled',
                    'severity': 'LOW'
                })
            
            # Check for CORS wildcard
            if re.search(r'allowed-origins\s*[:=]\s*\*', content, re.IGNORECASE):
                self.warnings.append({
                    'file': config_file,
                    'type': 'CORS allows all origins',
                    'severity': 'MEDIUM'
                })
            
            # Check for JWT secret length
            if re.search(r'jwt.*secret', content, re.IGNORECASE):
                for line in content.split('\n'):
                    if re.search(r'secret\s*[:=]', line, re.IGNORECASE):
                        match = re.search(r'secret\s*[:=]\s*["\']?([^"\'\s]+)', line, re.IGNORECASE)
                        if match:
                            secret = match.group(1)
                            if len(secret) < 32 and not re.search(r'\$\{|ENV', secret):
                                self.issues.append({
                                    'file': config_file,
                                    'type': 'JWT secret too short',
                                    'severity': 'MEDIUM',
                                    'details': f'Secret length: {len(secret)} (min: 32)'
                                })
            
        except Exception as e:
            pass  # Skip unreadable files
    
    def _generate_report(self):
        """Generate check report"""
        report_file = os.path.join(self.root_dir, 'config_check_report.txt')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("Configuration Files Check Report\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Files checked: {self.files_checked}\n")
            f.write(f"Root: {self.root_dir}\n\n")
            
            # Issues
            f.write("ISSUES\n")
            f.write("-" * 60 + "\n")
            
            if self.issues:
                for i, issue in enumerate(self.issues, 1):
                    f.write(f"\n{i}. [{issue['severity']}] {issue['type']}\n")
                    f.write(f"   File: {issue['file']}\n")
                    if 'details' in issue:
                        if isinstance(issue['details'], list):
                            for line_num, line_content in issue['details']:
                                f.write(f"   Line {line_num}: {line_content}\n")
                        else:
                            f.write(f"   Details: {issue['details']}\n")
            else:
                f.write("No issues found!\n")
            
            # Warnings
            f.write("\n\nWARNINGS\n")
            f.write("-" * 60 + "\n")
            
            if self.warnings:
                for i, warning in enumerate(self.warnings, 1):
                    f.write(f"\n{i}. [{warning['severity']}] {warning['type']}\n")
                    f.write(f"   File: {warning['file']}\n")
            else:
                f.write("No warnings!\n")
            
            # Summary
            f.write("\n\n" + "=" * 60 + "\n")
            f.write("SUMMARY\n")
            f.write("=" * 60 + "\n")
            f.write(f"Files checked: {self.files_checked}\n")
            f.write(f"Issues found: {len(self.issues)}\n")
            f.write(f"Warnings found: {len(self.warnings)}\n")
            
            if self.issues:
                f.write("\n⚠️  ACTION REQUIRED: Fix issues before deployment\n")
            else:
                f.write("\n✅ All checks passed!\n")
        
        print(f"\nReport: {report_file}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Files checked: {self.files_checked}")
        print(f"Issues: {len(self.issues)}")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.issues:
            print("\nIssues found:")
            for issue in self.issues[:10]:
                print(f"  - [{issue['severity']}] {issue['type']}")
                print(f"    {issue['file']}")
        
        if self.warnings:
            print(f"\nWarnings found: {len(self.warnings)}")
            
        print("\n" + "=" * 60)

def main():
    root_dir = r"d:\Developer\workplace\py\iteam\trae"
    checker = SimpleConfigChecker(root_dir)
    checker.check_all()

if __name__ == '__main__':
    main()
