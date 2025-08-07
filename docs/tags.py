from pathlib import Path
import re
import mkdocs_gen_files
from collections import defaultdict
# 引入拼音库用于中文首字母提取（需安装：pip install pypinyin）
from pypinyin import lazy_pinyin, Style

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
        # 处理列表格式（如tags: - 标签1 - 标签2）
        if line.strip().startswith('-') and 'tags' in metadata:
            # 这是标签列表项，添加到现有标签列表
            category = line.strip().lstrip('- ').strip()
            if category:
                metadata['tags'].append(category)
        elif ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key == 'tags' and value.startswith('-'):
                # 处理标签列表的第一个项（如tags: - 标签1）
                category = value.lstrip('- ').strip()
                metadata[key] = [category] if category else []
            elif key == 'tags':
                # 处理单标签情况（如tags: 标签1）
                metadata[key] = [value] if value else []
            else:
                metadata[key] = value
    return metadata

def get_first_letter(text):
    """获取文本的首字母（支持中文和英文）"""
    if not text:
        return '#'  # 空字符串用#分组
    
    # 处理英文
    if re.match(r'^[a-zA-Z]', text):
        return text[0].upper()
    
    # 处理中文
    pinyin = lazy_pinyin(text[0], style=Style.FIRST_LETTER)
    if pinyin and pinyin[0].isalpha():
        return pinyin[0].upper()
    
    # 其他情况（数字、符号等）
    return '#'

def generate_category_stats():
    # 博客文章存放目录
    blog_dir = Path('docs/blog/posts')
    if not blog_dir.exists():
        return "博客文章目录不存在"
    
    # 按标签统计文章数量（支持多标签）
    category_counts = defaultdict(int)
    
    for md_file in blog_dir.glob('*.md'):
        # 跳过列表页本身
        if md_file.name == 'index.md':
            continue
        
        # 提取元数据中的标签（支持列表格式）
        metadata = extract_metadata(md_file)
        tags = metadata.get('tags', [])
        
        if not tags:
            # 无标签的文章归类到"无标签"
            category_counts['无标签'] += 1
        else:
            # 多标签情况下，每个标签都计数
            for category in tags:
                category_counts[category] += 1
    
    # 按首字母分组
    groups = defaultdict(list)
    for category in category_counts:
        if category == '无标签':
            groups['无标签'].append((category, category_counts[category]))
        else:
            first_letter = get_first_letter(category)
            groups[first_letter].append((category, category_counts[category]))
    
    # 对每个分组内的标签按名称排序
    for key in groups:
        groups[key].sort(key=lambda x: x[0])  # 按标签名称排序
    
    # 对分组键进行排序（字母在前，#在后，最后是无标签）
    sorted_group_keys = sorted(
        [k for k in groups.keys() if k not in ('无标签', '#')],
        key=lambda x: x
    )
    # 添加#分组（如果有内容）
    if '#' in groups and groups['#']:
        sorted_group_keys.append('#')
    # 添加无标签到最后
    if '无标签' in groups and groups['无标签']:
        sorted_group_keys.append('无标签')
    
    # 生成Markdown内容
    markdown = "---\n"
    markdown += "title: '文章标签'\n"
    markdown += "date: 2025-01-30 19:13:23\n"
    markdown += "comments: false\n"
    markdown += "---\n\n"
    
    # 添加导航锚点
    markdown += "## 标签导航\n"
    markdown += " | ".join([f"[{key}](#{key.lower()})" for key in sorted_group_keys]) + "\n\n"
    
    # 按分组生成内容，每个字母一个表格
    for group_key in sorted_group_keys:
        # 添加分组标题和锚点
        markdown += f"### <a id='{group_key.lower()}'>{group_key}</a>\n\n"
        
        # 为每个分组创建独立表格
        markdown += "| 标签 | 文章总数 |\n"
        markdown += "|------|----------|\n"
        
        # 填充表格内容
        for category, count in groups[group_key]:
            markdown += f"| [{category}](/blog/category/{to_kebab_case(category)}/) | {count} |\n"
        
        markdown += "\n"  # 分组间增加空行
    
    return markdown

def to_kebab_case(text: str) -> str:
    """
    转换为适合URL的格式：
    - 英文转小写
    - 空格转换为连字符（多个空格合并）
    - 保留中文、数字和下划线
    - 移除感叹号等URL不安全的特殊字符
    """
    if not text:
        return "uncategorized"  # 空标签的默认值
    
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

# 生成标签统计页面
with mkdocs_gen_files.open('tags.md', 'w') as f:
    f.write(generate_category_stats())