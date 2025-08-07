from pathlib import Path
import re
import mkdocs_gen_files

def extract_metadata(file_path):
    """从Markdown文件中提取YAML元数据，支持列表类型的tags"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配YAML元数据块（---开头和结尾）
    metadata_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not metadata_match:
        return {}
    
    metadata = {}
    lines = metadata_match.group(1).split('\n')
    current_key = None
    current_value = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 检测新的键值对（非列表项）
        if ':' in line and not line.startswith('- '):
            if current_key is not None:
                # 保存上一个键的值
                if current_key == 'tags':
                    metadata[current_key] = [v.strip() for v in current_value]
                else:
                    metadata[current_key] = '\n'.join(current_value).strip()
            
            # 解析新的键
            key, value = line.split(':', 1)
            current_key = key.strip()
            current_value = [value.strip()] if value.strip() else []
        else:
            # 处理列表项（主要针对tags）
            if current_key == 'tags' and line.startswith('- '):
                current_value.append(line[2:].strip())
            elif current_key is not None:
                current_value.append(line)
    
    # 保存最后一个键的值
    if current_key is not None:
        if current_key == 'tags':
            metadata[current_key] = [v.strip() for v in current_value]
        else:
            metadata[current_key] = '\n'.join(current_value).strip()
    
    return metadata

def generate_blog_list():
    # 博客文章存放目录
    blog_dir = Path('docs/blog/posts')
    if not blog_dir.exists():
        return
    
    # 收集所有博客文章的元数据和路径
    posts = []
    for md_file in blog_dir.glob('*.md'):
        if md_file.name == 'index.md':
            continue
        
        metadata = extract_metadata(md_file)
        relative_path = md_file.relative_to('docs')
        # print('------------啊啊啊---------', "/"+str(relative_path))
        # 收集必要信息（包含标签）
        posts.append({
            'title': metadata.get('title', f'未命名文章：{md_file.stem}'),
            'date': metadata.get('date', ''),
            'summary': metadata.get('summary', '无摘要'),
            'path': "/blog/"+str(md_file.stem),
            'tags': metadata.get('tags', [])  # 新增标签字段
        })
    
    # 按日期倒序排序
    posts.sort(key=lambda x: x['date'], reverse=True)
    
    # 构建标签字典，按标签分组文章
    tags_dict = {}
    for post in posts:
        for tag in post['tags']:
            if tag not in tags_dict:
                tags_dict[tag] = []
            tags_dict[tag].append(post)
    
    # 按标签名称排序
    sorted_tags = sorted(tags_dict.keys())
    
    # 生成Markdown内容
    markdown = "# 博客文章列表\n\n"
    
    # 1. 所有文章按日期排序部分
    # markdown += "## 所有文章（按发布日期排序）\n\n"
    # for post in posts:
    #     markdown += f"### [{post['title']}]({post['path']})\n"
    #     markdown += f"**发布日期**：{post['date']}\n"
    #     if post['tags']:
    #         markdown += f"**标签**：{', '.join(post['tags'])}\n\n"
    #     else:
    #         markdown += "\n"
    #     markdown += f"{post['summary']}\n\n"
    #     markdown += "---\n\n"
    
    # 2. 按标签分类部分
    markdown += "## 按标签分类\n\n"
    for tag in sorted_tags:
        filename = f'blog/tags/{to_kebab_case(tag)}.md'
        # print('filename-------------', filename)
        markdown="" # 重置
        markdown = "---\n"
        markdown += f"title: '🏷️{tag}'\n"
        markdown += "date: 2025-01-30 19:13:23\n"
        markdown += "comments: false\n"
        markdown += "---\n\n"
        markdown += f"### [全部标签](/tags)\n\n"
        tag_posts = tags_dict[tag]
        for post in tag_posts:
            markdown += f"#### [{post['date']}] [{post['title']}]({post['path']})\n"
            # markdown += f"**发布日期**：{post['date']}\n\n"
            # markdown += f"{post['summary']}\n\n"
            markdown += "---\n\n"
        # 生成列表页到docs/blog/index.md
        # print('markdown-------------', markdown)
        with mkdocs_gen_files.open(filename, 'w') as f:
            f.write(markdown)
    return '123'
def to_kebab_case(text: str) -> str:
    """
    转换为适合URL的格式：
    - 英文转小写
    - 空格转换为连字符（多个空格合并）
    - 保留中文、数字和下划线
    - 移除感叹号等URL不安全的特殊字符
    """
    if not text:
        return "uncategorized"  # 空分类的默认值
    
    # 1. 转换为小写（仅对英文有效）
    lower_text = text.lower()
    
    # 2. 保留中文、字母、数字、下划线和空格，其他字符（如!、?、@等）全部移除
    # 中文范围：[\u4e00-\u9fa5]（基本汉字）
    cleaned = re.sub(r'[^\u4e00-\u9fa5a-z0-9_\s]', '', lower_text)
    
    # 3. 多个空格合并为一个，前后空格去除，再替换为连字符
    res = re.sub(r'\s+', '-', cleaned.strip())
    
    # 处理移除后可能为空的情况
    if not res:
        return "uncategorized"
    return res

#执行
print(generate_blog_list())