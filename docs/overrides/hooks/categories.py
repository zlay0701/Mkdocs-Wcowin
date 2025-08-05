import os
import fnmatch
from mkdocs.structure.pages import Page
from mkdocs.config.defaults import MkDocsConfig

# 改为嵌套结构，便于去重判断：{分类名: {页面URL: 页面信息}}
# 外层字典用分类名作为键，内层字典用页面URL作为键（确保唯一）
categories = {}
exclude_config = {
    "dirs": [],
    "files": [],
    "patterns": []
}

def normalize_path(path: str) -> str:
    """将路径中的反斜杠转换为正斜杠，统一路径格式"""
    if not path:
        return ""
    normalized = path.replace("\\", "/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    return normalized

def on_config(config: MkDocsConfig):
    """读取过滤配置并标准化路径"""
    global exclude_config
    raw_config = config.extra.get("exclude_categories", {})
    
    exclude_config["dirs"] = [
        normalize_path(dir_path) 
        for dir_path in (raw_config.get("dirs", []) if isinstance(raw_config.get("dirs", []), list) else [])
    ]
    exclude_config["files"] = [
        normalize_path(file_path) 
        for file_path in (raw_config.get("files", []) if isinstance(raw_config.get("files", []), list) else [])
    ]
    exclude_config["patterns"] = [
        normalize_path(pattern) 
        for pattern in (raw_config.get("patterns", []) if isinstance(raw_config.get("patterns", []), list) else [])
    ]
    
    print("\n===== 分类过滤规则（标准化后） =====")
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
    
    # 1. 目录过滤
    if exclude_config["dirs"]:
        for dir_pattern in exclude_config["dirs"]:
            normalized_dir = normalize_path(dir_pattern).rstrip("/") + "/"
            if src_path.startswith(normalized_dir):
                print(f"❌ 排除目录中的文档: {src_path}")
                print(f"   匹配规则: 目录 '{normalized_dir}'")
                return True
    
    # 2. 文件过滤
    if exclude_config["files"] and src_path in exclude_config["files"]:
        print(f"❌ 排除特定文件: {src_path}")
        print(f"   匹配规则: 文件列表")
        return True
    
    # 3. 模式过滤
    if exclude_config["patterns"]:
        for pattern in exclude_config["patterns"]:
            normalized_pattern = normalize_path(pattern)
            if normalized_pattern and fnmatch.fnmatch(src_path, normalized_pattern):
                print(f"❌ 排除模式匹配的文档: {src_path}")
                print(f"   匹配规则: 模式 '{normalized_pattern}'")
                return True
    
    return False

def on_page_markdown(markdown: str, page: Page, config: MkDocsConfig, **kwargs):
    """处理页面分类数据收集（增加去重逻辑）"""
    if is_excluded(page):
        return markdown
    
    page_url = page.url or "/"
    page_categories = page.meta.get("categories", [])
    
    # 处理分类格式
    if not isinstance(page_categories, list):
        original_value = page_categories
        page_categories = [str(original_value).strip() or "未分类"]
        print(f"⚠️ 页面 {page_url} 分类格式错误（原始值：{original_value}），自动修复为：{page_categories}")
    elif len(page_categories) == 0:
        page_categories = ["未分类"]
        print(f"✅ 页面 {page_url} 未设置分类，自动归类为：{page_categories}")
    else:
        print(f"✅ 页面 {page_url} 的分类：{page_categories}")
    
    # 收集分类数据（带去重判断）
    for cat in page_categories:
        cat_str = str(cat).strip() or "未分类"
        # 初始化分类字典（内层用URL作为唯一键）
        if cat_str not in categories:
            categories[cat_str] = {}
        
        # 检查页面URL是否已存在于当前分类中（去重核心逻辑）
        if page_url in categories[cat_str]:
            print(f"⚠️ 页面 {page_url} 在分类「{cat_str}」中已存在，跳过重复添加")
            continue
        
        # 添加新页面（用URL作为键，避免重复）
        categories[cat_str][page_url] = {
            "title": page.title,
            "url": page_url
        }
        print(f"➕ 页面 {page_url} 已添加到分类「{cat_str}」")
    
    return markdown

def on_env(env, config: MkDocsConfig,** kwargs):
    """传递分类数据到模板（转换为列表格式）"""
    # 将内层字典转换为列表（保留顺序）
    sorted_categories = {}
    for cat, pages_dict in sorted(categories.items()):
        # 按URL排序（可选，确保展示顺序一致）
        sorted_pages = sorted(pages_dict.values(), key=lambda x: x["url"])
        sorted_categories[cat] = sorted_pages
    
    env.globals["all_categories"] = sorted_categories
    
    # 打印去重后的汇总信息
    total_pages = sum(len(pages) for pages in sorted_categories.values())
    print("\n===== 分类处理汇总（去重后） =====")
    print(f"📊 参与分类的文档总数: {total_pages}")
    for cat, pages in sorted_categories.items():
        print(f"   分类「{cat}」包含 {len(pages)} 篇文档")
    print("====================================\n")
    
    return env
