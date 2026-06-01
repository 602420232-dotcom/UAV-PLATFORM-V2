"""
配置文件一致性检查工具
检查所有YAML配置文件的一致性和安全性
"""

import os
import yaml
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class ConfigChecker:
    """配置文件检查器"""
    
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.issues = []
        self.warnings = []
        self.info = []
        
    def check_all(self):
        """检查所有配置文件"""
        print("=" * 60)
        print("Configuration Files Consistency Checker")
        print("=" * 60)
        
        # 查找所有YAML文件
        yaml_files = self._find_yaml_files()
        print(f"\nFound {len(yaml_files)} YAML files\n")
        
        # 检查每个文件
        for yaml_file in yaml_files:
            self._check_yaml_file(yaml_file)
        
        # 检查Java配置文件
        self._check_java_properties()
        
        # 生成报告
        self._generate_report()
        
    def _find_yaml_files(self) -> List[str]:
        """查找所有YAML文件"""
        yaml_files = []
        exclude_dirs = {'__pycache__', '.git', '.idea', 'venv', 'env', 'node_modules'}
        
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith(('.yml', '.yaml')):
                    yaml_files.append(os.path.join(root, file))
        
        return yaml_files
    
    def _check_yaml_file(self, yaml_file: str):
        """检查单个YAML文件"""
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            if not config:
                return
                
            # 检查敏感配置
            self._check_security_config(yaml_file, config)
            
            # 检查配置一致性
            self._check_config_consistency(yaml_file, config)
            
        except Exception as e:
            self.warnings.append({
                'file': yaml_file,
                'issue': f'Failed to parse: {str(e)}'
            })
    
    def _check_security_config(self, yaml_file: str, config: Dict):
        """检查安全配置"""
        file_name = Path(yaml_file).name.lower()
        
        # 检查密码配置
        if 'password' in str(config).lower():
            if 'password' in config and isinstance(config['password'], str):
                if not any(marker in config.get('password', '') for marker in ['${', 'ENV', 'env', 'SECRET']):
                    self.issues.append({
                        'file': yaml_file,
                        'severity': 'HIGH',
                        'issue': 'Hardcoded password detected',
                        'recommendation': 'Use environment variables: password: ${DB_PASSWORD}'
                    })
        
        # 检查JWT配置
        if 'jwt' in str(config).lower() or 'secret' in str(config).lower():
            if config.get('jwt', {}).get('secret'):
                secret = config['jwt']['secret']
                if len(str(secret)) < 32 and not any(marker in str(secret) for marker in ['${', 'ENV']):
                    self.issues.append({
                        'file': yaml_file,
                        'severity': 'MEDIUM',
                        'issue': 'JWT secret too short (min 32 chars)',
                        'recommendation': 'Use strong secret or environment variable'
                    })
        
        # 检查调试模式
        if config.get('debug') == True:
            self.warnings.append({
                'file': yaml_file,
                'issue': 'Debug mode is enabled',
                'recommendation': 'Disable debug in production'
            })
        
        # 检查CORS配置
        if 'cors' in str(config).lower():
            cors_config = config.get('cors', {})
            if cors_config.get('allowed-origins') == '*':
                self.issues.append({
                    'file': yaml_file,
                    'severity': 'MEDIUM',
                    'issue': 'CORS allows all origins (*)',
                    'recommendation': 'Specify explicit allowed origins'
                })
    
    def _check_config_consistency(self, yaml_file: str, config: Dict):
        """检查配置一致性"""
        # 检查重复配置
        config_str = yaml.dump(config)
        
        # 检查硬编码URL
        if 'url' in config or 'endpoint' in config:
            url_pattern = r'https?://[^\s"\']+'
            urls = re.findall(url_pattern, config_str)
            
            if urls:
                self.info.append({
                    'file': yaml_file,
                    'type': 'URLs found',
                    'count': len(urls)
                })
        
        # 检查版本号
        if 'version' in config:
            version = config['version']
            if not re.match(r'^\d+\.\d+\.\d+$', str(version)):
                self.warnings.append({
                    'file': yaml_file,
                    'issue': f'Non-standard version format: {version}',
                    'recommendation': 'Use semantic versioning (e.g., 1.0.0)'
                })
    
    def _check_java_properties(self):
        """检查Java配置文件"""
        prop_files = []
        
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith('.properties'):
                    prop_files.append(os.path.join(root, file))
        
        for prop_file in prop_files:
            try:
                with open(prop_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 检查密码配置
                if 'password' in content.lower():
                    for line in content.split('\n'):
                        if 'password' in line.lower() and '=' in line:
                            key, value = line.split('=', 1)
                            value = value.strip()
                            if value and not any(marker in value for marker in ['${', 'ENV', '\\${']):
                                self.issues.append({
                                    'file': prop_file,
                                    'severity': 'HIGH',
                                    'line': line.strip(),
                                    'issue': 'Hardcoded password in properties file',
                                    'recommendation': 'Use environment variables'
                                })
                                
            except Exception as e:
                self.warnings.append({
                    'file': prop_file,
                    'issue': f'Failed to read: {str(e)}'
                })
    
    def _generate_report(self):
        """生成检查报告"""
        report_file = os.path.join(self.root_dir, 'config_check_report.txt')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("Configuration Files Check Report\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Root: {self.root_dir}\n\n")
            
            # Issues
            f.write("ISSUES (Require Immediate Attention)\n")
            f.write("-" * 60 + "\n")
            if self.issues:
                for i, issue in enumerate(self.issues, 1):
                    f.write(f"\n{i}. {issue['issue']}\n")
                    f.write(f"   File: {issue['file']}\n")
                    f.write(f"   Severity: {issue.get('severity', 'UNKNOWN')}\n")
                    f.write(f"   Recommendation: {issue.get('recommendation', 'N/A')}\n")
            else:
                f.write("No issues found!\n")
            
            # Warnings
            f.write("\n\nWARNINGS\n")
            f.write("-" * 60 + "\n")
            if self.warnings:
                for i, warning in enumerate(self.warnings, 1):
                    f.write(f"\n{i}. {warning['issue']}\n")
                    f.write(f"   File: {warning['file']}\n")
                    f.write(f"   Recommendation: {warning.get('recommendation', 'N/A')}\n")
            else:
                f.write("No warnings!\n")
            
            # Info
            f.write("\n\nINFO\n")
            f.write("-" * 60 + "\n")
            if self.info:
                for item in self.info:
                    f.write(f"\n{item['file']}: {item['type']} ({item['count']})\n")
            else:
                f.write("No additional info\n")
            
            # Summary
            f.write("\n\n" + "=" * 60 + "\n")
            f.write("SUMMARY\n")
            f.write("=" * 60 + "\n")
            f.write(f"Total Issues: {len(self.issues)}\n")
            f.write(f"Total Warnings: {len(self.warnings)}\n")
            f.write(f"Total Info: {len(self.info)}\n")
            
            if self.issues:
                f.write("\n⚠️  ACTION REQUIRED: Please fix all issues before deployment\n")
            else:
                f.write("\n✅ All checks passed!\n")
        
        print(f"\nReport generated: {report_file}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Issues: {len(self.issues)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Info: {len(self.info)}")
        
        if self.issues:
            print("\nTop issues:")
            for issue in self.issues[:5]:
                print(f"  - [{issue['severity']}] {issue['issue']}")
                print(f"    File: {issue['file']}")
        
        print("\n" + "=" * 60)

def main():
    root_dir = r"d:\Developer\workplace\py\iteam\trae"
    checker = ConfigChecker(root_dir)
    checker.check_all()

if __name__ == '__main__':
    main()
