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
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()
    return metadata

def generate_yearly_stats():
    # 博客文章存放目录
    blog_dir = Path('docs/blog/posts')
    if not blog_dir.exists():
        return "博客文章目录不存在"
    
    # 按年份统计文章数量
    year_counts = defaultdict(int)
    
    for md_file in blog_dir.glob('*.md'):
        # 跳过列表页本身
        if md_file.name == 'index.md':
            continue
        
        # 提取元数据中的日期
        metadata = extract_metadata(md_file)
        date = metadata.get('date', '')
        if date:
            year = date.split('-')[0]
            year_counts[year] += 1
        else:
            # 无日期的文章归类到"未知年份"
            year_counts['未知年份'] += 1
    
    # 按年份倒序排序（最新年份在前）
    sorted_years = sorted(year_counts.keys(), reverse=True, key=lambda x: x if x != '未知年份' else '0000')
    markdown = "---\n"
    markdown += "title: '归档'\n"
    markdown += "date: 2025-01-30 19:13:23\n"
    markdown += "comments: false\n"
    markdown += "---\n"
    # 生成统计结果Markdown
    # markdown += "# 归档\n\n"
    markdown += "| 年份 | 文章总数 |\n"
    markdown += "|------|----------|\n"
    
    for year in sorted_years:
        markdown += f"| [{year}年](/blog/archive/{year}/) | {year_counts[year]} |\n"
    
    return markdown


# 生成统计页面
with mkdocs_gen_files.open('foo.md', 'w') as f:
    f.write(generate_yearly_stats())