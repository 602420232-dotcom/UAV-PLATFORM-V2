"""
Python类型注解自动添加器
自动为关键函数添加类型注解（基于ast模块）
"""

import ast
import os
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

class TypeAnnotationAdder(ast.NodeVisitor):
    """Python AST访问器，为函数添加类型注解"""
    
    def __init__(self):
        self.modified = False
        self.changes = []
        
    def visit_FunctionDef(self, node):
        """检查并添加类型注解"""
        has_annotations = (
            node.returns is not None or  # 返回类型
            any(arg.annotation is not None for arg in node.args.args)  # 参数类型
        )
        
        if not has_annotations and len(node.args.args) <= 3:
            # 只处理参数较少的函数
            arg_names = [arg.arg for arg in node.args.args]
            
            # 智能推断类型
            inferred_types = self._infer_types(arg_names, node.name)
            
            if inferred_types:
                self.changes.append({
                    'function': node.name,
                    'args': arg_names,
                    'types': inferred_types
                })
                
        self.generic_visit(node)
    
    def _infer_types(self, arg_names: List[str], func_name: str) -> Optional[List[str]]:
        """根据参数名推断类型"""
        type_mapping = {
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
        }
        
        types = []
        for name in arg_names:
            if name in type_mapping:
                types.append(type_mapping[name])
            else:
                types.append('Any')
                
        return types

def add_types_to_file(file_path: str) -> Tuple[bool, List[dict]]:
    """为单个文件添加类型注解"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        adder = TypeAnnotationAdder()
        adder.visit(tree)
        
        if adder.changes:
            return True, adder.changes
        return False, []
        
    except Exception as e:
        return False, []

def scan_python_files(root_dir: str, extensions: List[str] = ['.py']) -> List[str]:
    """扫描所有Python文件"""
    python_files = []
    exclude_dirs = {'__pycache__', '.git', '.idea', 'venv', 'env', 'node_modules', 'build', 'dist'}
    
    for root, dirs, files in os.walk(root_dir):
        # 排除目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                python_files.append(os.path.join(root, file))
                
    return python_files

def generate_typed_wrapper(original_file: str, functions: List[dict]) -> str:
    """为函数生成带类型注解的包装器"""
    wrapper_lines = [
        "# 类型注解建议（请手动验证后应用）",
        f"# 文件: {original_file}",
        f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "'''",
        "类型注解建议：",
        ""
    ]
    
    for func in functions:
        wrapper_lines.append(f"def {func['function']}({', '.join(func['args'])}):")
        wrapper_lines.append(f"    # 建议类型: {dict(zip(func['args'], func['types']))}")
        wrapper_lines.append("    pass")
        wrapper_lines.append("")
    
    wrapper_lines.append("'''")
    
    return '\n'.join(wrapper_lines)

def main():
    """主函数"""
    print("=" * 60)
    print("Python类型注解自动添加器")
    print("=" * 60)
    
    # 扫描项目根目录
    root_dir = r"d:\Developer\workplace\py\iteam\trae"
    
    print(f"\n正在扫描: {root_dir}")
    python_files = scan_python_files(root_dir)
    print(f"找到 {len(python_files)} 个Python文件\n")
    
    # 分析并生成建议
    all_changes = []
    
    for i, file_path in enumerate(python_files, 1):
        if i % 20 == 0:
            print(f"进度: {i}/{len(python_files)}...")
            
        modified, changes = add_types_to_file(file_path)
        if changes:
            all_changes.append({
                'file': file_path,
                'changes': changes
            })
    
    print(f"\n分析完成！")
    print(f"找到 {len(all_changes)} 个文件可以添加类型注解")
    print(f"总计 {sum(len(c['changes']) for c in all_changes)} 个函数")
    
    # 生成报告
    if all_changes:
        report_file = os.path.join(root_dir, 'type_annotations_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("Python类型注解建议报告\n")
            f.write("=" * 60 + "\n\n")
            
            for item in all_changes:
                f.write(f"文件: {item['file']}\n")
                for change in item['changes']:
                    f.write(f"  函数: {change['function']}\n")
                    f.write(f"  参数类型: {dict(zip(change['args'], change['types']))}\n")
                f.write("\n")
                
        print(f"\n报告已生成: {report_file}")
        
        # 显示示例
        print("\n示例（前10个）：")
        for item in all_changes[:10]:
            print(f"\n{item['file']}")
            for change in item['changes'][:3]:
                print(f"  {change['function']}({', '.join(change['args'])}) -> {dict(zip(change['args'], change['types']))}")
    
    print("\n" + "=" * 60)
    print("提示：此工具提供类型注解建议，请手动验证后应用")
    print("=" * 60)

if __name__ == '__main__':
    main()
