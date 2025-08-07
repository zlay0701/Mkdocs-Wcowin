from pathlib import Path
import re
import mkdocs_gen_files
from collections import defaultdict

def extract_metadata(file_path):
    """从Markdown文件中提取YAML元数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配YAML元数据块（---开头和结尾）
    metadata_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not metadata_match:
        return {}
    
    metadata = {}
    for line in metadata_match.group(1).split('\n'):
        # 处理列表格式（如categories: - 分类1 - 分类2）
        if line.strip().startswith('-') and 'categories' in metadata:
            # 这是分类列表项，添加到现有分类列表
            category = line.strip().lstrip('- ').strip()
            if category:
                metadata['categories'].append(category)
        elif ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key == 'categories' and value.startswith('-'):
                # 处理分类列表的第一个项（如categories: - 分类1）
                category = value.lstrip('- ').strip()
                metadata[key] = [category] if category else []
            elif key == 'categories':
                # 处理单分类情况（如categories: 分类1）
                metadata[key] = [value] if value else []
            else:
                metadata[key] = value
    return metadata

def generate_category_stats():
    # 博客文章存放目录
    blog_dir = Path('docs/blog/posts')
    if not blog_dir.exists():
        return "博客文章目录不存在"
    
    # 按分类统计文章数量（支持多分类）
    category_counts = defaultdict(int)
    
    for md_file in blog_dir.glob('*.md'):
        # 跳过列表页本身
        if md_file.name == 'index.md':
            continue
        
        # 提取元数据中的分类（支持列表格式）
        metadata = extract_metadata(md_file)
        categories = metadata.get('categories', [])
        
        if not categories:
            # 无分类的文章归类到"未分类"
            category_counts['未分类'] += 1
        else:
            # 多分类情况下，每个分类都计数
            for category in categories:
                category_counts[category] += 1
    
    # 按分类名称A-Z排序（"未分类"排在最后）
    sorted_categories = sorted(
        category_counts.keys(),
        key=lambda x: x if x != '未分类' else 'zzzzz'  # 确保"未分类"在最后
    )
    
    # 生成Markdown内容
    markdown = "---\n"
    markdown += "title: '文章分类'\n"
    markdown += "date: 2025-01-30 19:13:23\n"
    markdown += "comments: false\n"
    markdown += "---\n\n"
    
    markdown += "| 分类 | 文章总数 |\n"
    markdown += "|------|----------|\n"
    
    for category in sorted_categories:
        # 分类页面链接（根据实际站点结构调整）
        markdown += f"| [{category}](/blog/categories/{category}/) | {category_counts[category]} |\n"
    
    return markdown


# 生成分类统计页面
with mkdocs_gen_files.open('categories.md', 'w') as f:
    f.write(generate_category_stats())
