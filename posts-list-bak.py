from pathlib import Path
import re
import mkdocs_gen_files

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
            'date': metadata.get('date', ''),  # 假设格式为YYYY-MM-DD
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