from pathlib import Path
import re
import mkdocs_gen_files
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
def generate_blog_list():
    # 博客文章存放目录（根据实际情况修改）
    blog_dir = Path('docs/blog/posts')
    if not blog_dir.exists():
        return
    
    # 收集所有博客文章的元数据和路径
    posts = []
    for md_file in blog_dir.glob('*.md'):
        # 跳过列表页本身（如果有的话）
        if md_file.name == 'index.md':
            continue
        
        # 提取元数据
        metadata = extract_metadata(md_file)
        # 文章相对路径（用于生成链接）
        relative_path = md_file.relative_to('docs')
        
        # 收集必要信息（标题、日期、摘要、路径）
        posts.append({
            'title': metadata.get('title', f'未命名文章：{md_file.stem}'),
            'date': unify_date_type(metadata.get('date', '')),  # 假设格式为YYYY-MM-DD
            'summary': metadata.get('summary', '无摘要'),
            'path': str(relative_path)
        })
    
    # 按日期倒序排序（最新文章在前）
    posts.sort(key=lambda x: x['date'], reverse=True)
    
    # 生成Markdown列表内容
    markdown = "# 博客文章列表\n\n"
    markdown += "以下是所有博客文章，按发布日期排序：\n\n"
    
    for post in posts:
        markdown += f"## [{post['title']}]({post['path']})\n"
        markdown += f"**发布日期**：{post['date']}\n\n"
        markdown += f"{post['summary']}\n\n"
        markdown += "---\n\n"
    
    # 生成列表页（输出到docs/blog/index.md）
    # print('markdown|', markdown)
    return markdown
    

# 供mkdocs-gen-files调用的入口函数
    # generate_blog_list()
with mkdocs_gen_files.open('foo.md', 'w') as f:
        f.write(generate_blog_list())