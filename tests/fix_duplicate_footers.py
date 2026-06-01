#!/usr/bin/env python3
"""
修复重复的页脚问题
删除所有旧的页脚，只保留统一的新页脚
"""
import os
import re

def fix_duplicate_footers(root_dir):
    """
    修复所有md文件中的重复页脚
    """
    # 统一的新页脚
    new_footer = """
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
"""
    
    # 匹配各种旧页脚格式的正则
    old_footer_patterns = [
        # 匹配无引用标记的格式
        r'\*\*最后更新\*\*:.*?\n\*\*版本\*\*:.*?\n\*\*维护者\*\*:.*?(?=\n---|\Z)',
        # 匹配另一种无引用格式
        r'最后更新:.*?\n版本:.*?\n维护者:.*?(?=\n---|\Z)',
        # 匹配有分隔线但内容不同的
        r'---\s*\n\*\*最后更新\*\*:.*?\n\*\*文档版本\*\*:.*?\n\*\*维护者\*\*:.*?(?=\n---|\Z)',
    ]
    
    fixed_count = 0
    skipped_count = 0
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # 跳过一些不需要的目录
        if any(part in ['.git', 'node_modules', 'venv', '__pycache__'] for part in dirpath.split(os.sep)):
            continue
            
        for filename in filenames:
            if filename.endswith('.md'):
                filepath = os.path.join(dirpath, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # 1. 移除所有旧的页脚（任何包含"最后更新"但没有>标记的）
                    for pattern in old_footer_patterns:
                        content = re.sub(pattern, '', content, flags=re.DOTALL)
                    
                    # 2. 移除重复的新页脚（只保留最后一个）
                    # 先移除所有现有的新页脚
                    new_footer_pattern = r'---\s*\n> \*\*最后更新\*\*: 2026-05-08  \n> \*\*版本\*\*: 2\.1  \n> \*\*维护者\*\*: DITHIOTHREITOL'
                    content = re.sub(new_footer_pattern, '', content)
                    
                    # 清理多余的空行和分隔线
                    content = re.sub(r'\n{3,}', '\n\n', content)
                    content = re.sub(r'---\s*\n\s*---', '---', content)
                    
                    # 3. 在文件末尾添加统一的新页脚
                    # 先移除末尾多余的空行
                    content = content.rstrip()
                    
                    # 如果最后已经有分隔线，就不再添加
                    if not content.endswith('---'):
                        content += new_footer
                    else:
                        # 替换最后的分隔线为完整页脚
                        content = content.rstrip('- ')
                        content += new_footer
                    
                    # 只在内容实际改变时才写入文件
                    if content != original_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"✅ 修复: {filepath}")
                        fixed_count += 1
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    print(f"❌ 错误处理 {filepath}: {e}")
    
    print(f"\n📊 完成! 修复了 {fixed_count} 个文件, 跳过 {skipped_count} 个文件")

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"🚀 开始修复重复页脚问题，根目录: {root_dir}\n")
    fix_duplicate_footers(root_dir)
