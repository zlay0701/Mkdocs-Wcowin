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
        tags = metadata.get('tags', [])
        tags = [tag for tag in tags if tag.strip()]
        # 若过滤后仍为空，则设置默认标签['无标签']
        if not tags:
            tags = ['无标签']
        # 收集必要信息（包含标签）
        posts.append({
            'title': metadata.get('title', f'未命名文章：{md_file.stem}'),
            'date': unify_date_type(metadata.get('date', '')),
            'summary': metadata.get('summary', '无摘要'),
            'path': "../../"+str(relative_path),
            'tags': tags  # 新增标签字段
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
        markdown += f"### [全部标签](../../tags.md)\n\n"
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