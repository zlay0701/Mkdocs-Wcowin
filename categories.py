from pathlib import Path
import re
import mkdocs_gen_files
from collections import defaultdict
# 引入拼音库用于中文首字母提取（需安装：pip install pypinyin）
from pypinyin import lazy_pinyin, Style
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
    
    # 按首字母分组
    groups = defaultdict(list)
    for category in category_counts:
        if category == '未分类':
            groups['未分类'].append((category, category_counts[category]))
        else:
            first_letter = get_first_letter(category)
            groups[first_letter].append((category, category_counts[category]))
    
    # 对每个分组内的分类按名称排序
    for key in groups:
        groups[key].sort(key=lambda x: x[0])  # 按分类名称排序
    
    # 对分组键进行排序（字母在前，#在后，最后是未分类）
    sorted_group_keys = sorted(
        [k for k in groups.keys() if k not in ('未分类', '#')],
        key=lambda x: x
    )
    # 添加#分组（如果有内容）
    if '#' in groups and groups['#']:
        sorted_group_keys.append('#')
    # 添加未分类到最后
    if '未分类' in groups and groups['未分类']:
        sorted_group_keys.append('未分类')
    
    # 生成Markdown内容
    markdown = "---\n"
    markdown += "title: '文章分类'\n"
    markdown += "date: 2025-01-30 19:13:23\n"
    markdown += "comments: false\n"
    markdown += "---\n\n"
    
    # 添加导航锚点
    markdown += "## 分类导航\n"
    markdown += " | ".join([f"[{key}](#{key.lower()})" for key in sorted_group_keys]) + "\n\n"
    
    # 按分组生成内容，每个字母一个表格
    for group_key in sorted_group_keys:
        # 添加分组标题和锚点
        markdown += f"### <a id='{group_key.lower()}'>{group_key}</a>\n\n"
        
        # 为每个分组创建独立表格
        markdown += "| 分类 | 文章总数 |\n"
        markdown += "|------|----------|\n"
        
        # 填充表格内容
        for category, count in groups[group_key]:
            markdown += f"| [{category}](blog/category/{to_kebab_case(category)}.md) | {count} |\n"
        
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

# 生成分类统计页面
with mkdocs_gen_files.open('categories.md', 'w') as f:
    f.write(generate_category_stats())