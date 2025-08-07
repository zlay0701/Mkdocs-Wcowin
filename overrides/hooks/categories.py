import os
import fnmatch
import re
from mkdocs.structure.pages import Page
from mkdocs.config.defaults import MkDocsConfig

# 新增debug参数控制打印输出
debug = False  # 设置为True开启调试打印，False关闭

# 数据结构调整为: {分类名: {"url": 分类URL, "pages": {页面URL: 页面信息}}}
categories = {}
exclude_config = {
    "dirs": [],
    "files": [],
    "patterns": []
}
# 新增包含目录配置
include_config = {
    "dirs": []
}

def normalize_path(path: str) -> str:
    """将路径中的反斜杠转换为正斜杠，统一路径格式"""
    if not path:
        return ""
    normalized = path.replace("\\", "/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    return normalized

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

def on_config(config: MkDocsConfig):
    """读取过滤配置并标准化路径"""
    global exclude_config, include_config, debug  # 引用全局debug变量
    
    # 从配置中读取debug模式（如果有），否则使用默认值
    debug = config.extra.get("categories_debug", debug)
    
    # 处理排除配置
    raw_exclude_config = config.extra.get("exclude_categories", {})
    exclude_config["dirs"] = [
        normalize_path(dir_path) 
        for dir_path in (raw_exclude_config.get("dirs", []) if isinstance(raw_exclude_config.get("dirs", []), list) else [])
    ]
    exclude_config["files"] = [
        normalize_path(file_path) 
        for file_path in (raw_exclude_config.get("files", []) if isinstance(raw_exclude_config.get("files", []), list) else [])
    ]
    exclude_config["patterns"] = [
        normalize_path(pattern) 
        for pattern in (raw_exclude_config.get("patterns", []) if isinstance(raw_exclude_config.get("patterns", []), list) else [])
    ]
    
    # 新增：处理包含配置
    raw_include_config = config.extra.get("include_categories", {})
    include_config["dirs"] = [
        normalize_path(dir_path) 
        for dir_path in (raw_include_config.get("dirs", []) if isinstance(raw_include_config.get("dirs", []), list) else [])
    ]
    
    # 仅在debug模式下打印
    if debug:
        print("\n===== 分类过滤规则（标准化后） =====")
        print(f"包含目录: {include_config['dirs']}")
        print(f"排除目录: {exclude_config['dirs']}")
        print(f"排除文件: {exclude_config['files']}")
        print(f"排除模式: {exclude_config['patterns']}")
        print("====================================\n")
    return config

def is_excluded(page: Page) -> bool:
    """判断页面是否需要被排除（处理路径分隔符）"""
    try:
        src_path = page.file.src_path
    except AttributeError:
        src_path = getattr(page, 'src_path', '')
    
    src_path = normalize_path(src_path)
    
    if not src_path:
        return False
    
    # 新增：包含目录过滤（白名单机制）
    if include_config["dirs"]:
        included = False
        for dir_pattern in include_config["dirs"]:
            normalized_dir = normalize_path(dir_pattern).rstrip("/") + "/"
            if src_path.startswith(normalized_dir):
                included = True
                break
        if not included:
            # 仅在debug模式下打印
            if debug:
                print(f"❌ 不在包含目录中的文档: {src_path}")
                print(f"   包含目录: {include_config['dirs']}")
            return True
    
    # 1. 目录过滤
    if exclude_config["dirs"]:
        for dir_pattern in exclude_config["dirs"]:
            normalized_dir = normalize_path(dir_pattern).rstrip("/") + "/"
            if src_path.startswith(normalized_dir):
                # 仅在debug模式下打印
                if debug:
                    print(f"❌ 排除目录中的文档: {src_path}")
                    print(f"   匹配规则: 目录 '{normalized_dir}'")
                return True
    
    # 2. 文件过滤
    if exclude_config["files"] and src_path in exclude_config["files"]:
        # 仅在debug模式下打印
        if debug:
            print(f"❌ 排除特定文件: {src_path}")
            print(f"   匹配规则: 文件列表")
        return True
    
    # 3. 模式过滤
    if exclude_config["patterns"]:
        for pattern in exclude_config["patterns"]:
            normalized_pattern = normalize_path(pattern)
            if normalized_pattern and fnmatch.fnmatch(src_path, normalized_pattern):
                # 仅在debug模式下打印
                if debug:
                    print(f"❌ 排除模式匹配的文档: {src_path}")
                    print(f"   匹配规则: 模式 '{normalized_pattern}'")
                return True
    
    return False

# 以下on_page_markdown和on_env函数保持不变
def on_page_markdown(markdown: str, page: Page, config: MkDocsConfig, **kwargs):
    """处理页面分类数据收集（增加分类URL支持和去重逻辑）"""
    if is_excluded(page):
        return markdown
    
    page_url = page.url or "/"
    page_categories = page.meta.get("categories", [])
    
    # 处理分类格式
    if not isinstance(page_categories, list):
        original_value = page_categories
        page_categories = [{"name": str(original_value).strip() or "未分类", "url": ""}]
        # 仅在debug模式下打印
        if debug:
            print(f"⚠️ 页面 {page_url} 分类格式错误（原始值：{original_value}），自动修复为：[{page_categories[0]['name']}]")
    elif len(page_categories) == 0:
        page_categories = [{"name": "未分类", "url": ""}]
        # 仅在debug模式下打印
        if debug:
            print(f"✅ 页面 {page_url} 未设置分类，自动归类为：[{page_categories[0]['name']}]")
    else:
        # 统一转换为字典格式，支持字符串和字典混合输入
        normalized_cats = []
        for cat in page_categories:
            if isinstance(cat, dict):
                name = str(cat.get("name", "")).strip() or "未分类"
                url = normalize_path(str(cat.get("url", "")))
                normalized_cats.append({"name": name, "url": url})
            else:
                name = str(cat).strip() or "未分类"
                normalized_cats.append({"name": name, "url": ""})
        page_categories = normalized_cats
        # 仅在debug模式下打印
        if debug:
            print(f"✅ 页面 {page_url} 的分类：{[cat['name'] for cat in page_categories]}")
    
    # 收集分类数据（带去重和URL处理）
    for cat in page_categories:
        cat_name = cat["name"]
        cat_url = cat["url"]
        
        # 初始化分类字典
        if cat_name not in categories:
            # 自动生成分类URL：/blog/category/kebab-case名称
            generated_url = f"/blog/category/{to_kebab_case(cat_name)}"
            categories[cat_name] = {
                "url": cat_url or generated_url,  # 优先使用用户指定的URL，否则使用生成的
                "pages": {}
            }
        else:
            # 处理分类URL冲突
            existing_url = categories[cat_name]["url"]
            if existing_url and cat_url and existing_url != cat_url:
                # 仅在debug模式下打印
                if debug:
                    print(f"⚠️ 分类「{cat_name}」URL冲突，现有: {existing_url}, 新值: {cat_url}，保留现有值")
            # 用非空URL更新（确保优先保留已设置的URL）
            if not existing_url:
                # 如果现有URL为空，生成并设置URL
                generated_url = f"/blog/category/{to_kebab_case(cat_name)}"
                categories[cat_name]["url"] = cat_url or generated_url
        
        # 处理页面去重
        pages_dict = categories[cat_name]["pages"]
        if page_url in pages_dict:
            # 仅在debug模式下打印
            if debug:
                print(f"⚠️ 页面 {page_url} 在分类「{cat_name}」中已存在，跳过重复添加")
            continue
        
        # 添加新页面
        pages_dict[page_url] = {
            "title": page.title,
            "url": "/" + page_url.lstrip("/")  # 确保URL格式统一
        }
        # 仅在debug模式下打印
        if debug:
            print(f"➕ 页面 {page_url} 已添加到分类「{cat_name}」")
    
    return markdown

def on_env(env, config: MkDocsConfig,** kwargs):
    """传递分类数据到模板（包含分类URL）"""
    # 整理分类数据并排序
    sorted_categories = {}
    for cat_name in sorted(categories.keys()):
        cat_data = categories[cat_name]
        # 排序页面
        sorted_pages = sorted(cat_data["pages"].values(), key=lambda x: x["url"])
        sorted_categories[cat_name] = {
            "url": cat_data["url"],
            "pages": sorted_pages
        }
    
    env.globals["all_categories"] = sorted_categories
    
    # 仅在debug模式下打印汇总信息
    if debug:
        total_pages = sum(len(cat["pages"]) for cat in sorted_categories.values())
        print("\n===== 分类处理汇总（去重后） =====")
        print(f"📊 参与分类的文档总数: {total_pages}")
        for cat_name, cat_data in sorted_categories.items():
            print(f"   分类「{cat_name}」(URL: {cat_data['url']}) 包含 {len(cat_data['pages'])} 篇文档")
        print("====================================\n")
    
    return env