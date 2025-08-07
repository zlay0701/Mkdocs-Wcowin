from pathlib import Path
import re
import mkdocs_gen_files
from collections import defaultdict
import yaml
from datetime import datetime, date
def extract_metadata(file_path):
    """使用PyYAML解析Markdown文件中的YAML元数据"""
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配YAML元数据块（---开头和结尾）
        if not content.startswith('---\n'):
            return {}
        
        # 分割元数据块和正文
        metadata_end = content.find('\n---', 4)  # 从第4个字符开始找（跳过开头的---\n）
        if metadata_end == -1:
            return {}
        
        # 提取YAML元数据部分
        yaml_content = content[4:metadata_end].strip()  # 去掉开头的---\n和结尾的\n
        if not yaml_content:
            return {}
        
        # 使用PyYAML解析YAML内容
        metadata = yaml.safe_load(yaml_content)
        
        # 确保返回字典类型（处理空元数据的情况）
        return metadata if isinstance(metadata, dict) else {}
    
    except Exception as e:
        print(f"解析元数据出错（{file_path}）：{str(e)}")
        return {}

def unify_date_type(date_value):
    """
    将所有日期统一转换为datetime.date类型
    处理字符串、datetime、date等多种输入
    """
    if isinstance(date_value, datetime):
        # datetime -> date（提取日期部分，忽略时间）
        return date_value.date()
    elif isinstance(date_value, date):
        # 已经是date类型，直接返回
        return date_value
    elif isinstance(date_value, str):
        # 字符串尝试解析为date
        date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y年%m月%d日'
        ]
        for fmt in date_formats:
            try:
                return datetime.strptime(date_value, fmt).date()
            except ValueError:
                continue
        # 解析失败返回一个极小日期（确保能参与排序）
        return date.min
    else:
        # 未知类型返回极小日期
        return date.min
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
            year = str(date).split('-')[0]
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
with mkdocs_gen_files.open('archives.md', 'w') as f:
    f.write(generate_yearly_stats())