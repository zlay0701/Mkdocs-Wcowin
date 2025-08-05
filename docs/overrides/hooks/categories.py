import os
import fnmatch
from mkdocs.structure.pages import Page
from mkdocs.config.defaults import MkDocsConfig

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
    # 替换反斜杠为正斜杠
    normalized = path.replace("\\", "/")
    # 处理连续斜杠（如"a//b" -> "a/b"）
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    return normalized

def on_config(config: MkDocsConfig):
    """读取过滤配置并标准化路径"""
    global exclude_config
    raw_config = config.extra.get("exclude_categories", {})
    
    # 标准化所有配置路径为正斜杠
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
    # 获取并标准化文件路径
    try:
        src_path = page.file.src_path
    except AttributeError:
        src_path = getattr(page, 'src_path', '')
    
    # 标准化页面路径为正斜杠
    src_path = normalize_path(src_path)
    
    if not src_path:
        return False
    
    # 1. 目录过滤
    if exclude_config["dirs"]:
        for dir_pattern in exclude_config["dirs"]:
            # 标准化目录模式并确保以斜杠结尾
            normalized_dir = normalize_path(dir_pattern).rstrip("/") + "/"
            if src_path.startswith(normalized_dir):
                print(f"❌ 排除目录中的文档: {src_path}")
                print(f"   匹配规则: 目录 '{normalized_dir}'")
                return True
    
    # 2. 文件过滤
    if exclude_config["files"]:
        if src_path in exclude_config["files"]:
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
    """处理页面分类数据收集"""
    if is_excluded(page):
        return markdown
    
    page_url = page.url or "/"
    page_categories = page.meta.get("categories", [])
    
    if not isinstance(page_categories, list):
        original_value = page_categories
        page_categories = [str(original_value).strip() or "未分类"]
        print(f"⚠️ 页面 {page_url} 分类格式错误（原始值：{original_value}），自动修复为：{page_categories}")
    elif len(page_categories) == 0:
        page_categories = ["未分类"]
        print(f"✅ 页面 {page_url} 未设置分类，自动归类为：{page_categories}")
    else:
        print(f"✅ 页面 {page_url} 的分类：{page_categories}")
    
    for cat in page_categories:
        cat_str = str(cat).strip() or "未分类"
        if cat_str not in categories:
            categories[cat_str] = []
        categories[cat_str].append({
            "title": page.title,
            "url": page_url
        })
    
    return markdown

def on_env(env, config: MkDocsConfig,** kwargs):
    """传递分类数据到模板"""
    sorted_categories = dict(sorted(categories.items()))
    env.globals["all_categories"] = sorted_categories
    
    print("\n===== 分类处理汇总 =====")
    print(f"📊 参与分类的文档总数: {sum(len(pages) for pages in sorted_categories.values())}")
    print("=======================\n")
    
    return env
