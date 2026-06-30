"""
MCP 工具模块 —— 标准化文件系统操作接口
==========================================
功能：
  1. mcp_list_products()   —— 列出产品目录下所有文件
  2. mcp_get_product()     —— 读取指定产品文件的详细内容
  3. mcp_search_catalog()  —— 在所有产品文件中搜索关键词

比喻：AI 工具的「USB 标准」——不管什么功能，都用同一套 JSON 协议调用。
"""
import os


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CATALOG_DIR = os.path.join(project_root, "data", "product_catalog")


# ==================== 工具 1：列出产品文件 ====================
def mcp_list_products() -> str:
    """列出产品目录下所有文件的名称和大小。"""
    try:
        files = os.listdir(CATALOG_DIR)
        if not files:
            return "产品目录为空，暂无文件。"
        lines = [f"产品目录文件列表（共 {len(files)} 个）："]
        for i, f in enumerate(files, 1):
            fpath = os.path.join(CATALOG_DIR, f)
            size  = os.path.getsize(fpath)
            lines.append(f"  {i}. {f}  ({size} 字节)")
        return "\n".join(lines)
    except Exception as e:
        return f"列出文件出错：{e}"


# ==================== 工具 2：读取产品文件 ====================
def mcp_get_product(filename: str) -> str:
    """读取指定产品文件的完整内容。含路径穿越防护。"""
    if ".." in filename or "/" in filename or "\\" in filename:
        return "错误：文件名包含不安全字符，禁止路径穿越。"

    filepath = os.path.join(CATALOG_DIR, filename)
    if not os.path.exists(filepath):
        available = ", ".join(os.listdir(CATALOG_DIR))
        return f"文件不存在：{filename}\n当前目录可用文件：{available}"

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return f"文件「{filename}」完整内容：\n\n{content}"
    except Exception as e:
        return f"读取文件出错：{e}"


# ==================== 工具 3：搜索产品目录 ====================
def mcp_search_catalog(query: str) -> str:
    """在所有产品目录文件中搜索关键词（不区分大小写）。"""
    try:
        results = []
        for filename in os.listdir(CATALOG_DIR):
            filepath = os.path.join(CATALOG_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line_no, line in enumerate(f, 1):
                        if query.lower() in line.lower():
                            results.append(f"  [{filename}:L{line_no}] {line.strip()}")
            except Exception:
                continue

        if results:
            return f"搜索「{query}」找到 {len(results)} 条结果：\n" + "\n".join(results[:20])
        return f"搜索「{query}」未找到匹配的产品信息。"
    except Exception as e:
        return f"搜索出错：{e}"


# ==================== MCP 工具注册表 ====================
MCP_TOOLS = {
    "list_products": {
        "function": mcp_list_products,
        "description": "列出产品目录下所有文件的名称和大小",
        "parameters": {},
    },
    "get_product": {
        "function": mcp_get_product,
        "description": "读取指定产品文件的完整内容（包括产品参数、规格、价格等）",
        "parameters": {"filename": "文件名，如 '产品清单.txt'"},
    },
    "search_catalog": {
        "function": mcp_search_catalog,
        "description": "在产品目录文件中搜索关键词，返回所有匹配的行",
        "parameters": {"query": "搜索关键词"},
    },
}
