"""
RAG 检索模块 —— 产品手册语义搜索
====================================
功能：
  1. init_rag()    —— 启动时调用：加载 BGE-M3 + 切分文档 + 向量入库
  2. search(query) —— 每次对话调用：语义检索 Top-K 片段

数据流：
  产品手册.txt → chunk_text() 切分 → BGE-M3 编码 → Chroma 入库
  用户问题    → BGE-M3 编码 → Chroma 查询 → Top-K 片段 → 拼接返回
"""
import os
import sys
import chromadb
from FlagEmbedding import BGEM3FlagModel


# 动态路径配置
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_PATH  = os.path.abspath(os.path.join(project_root, "..", "bge-m3"))
MANUAL_DIR  = os.path.join(project_root, "data", "product_manual")
CHROMA_PATH = os.path.join(project_root, "chroma_db")

# 全局变量
_embed_model = None
_collection  = None
_ready       = False


def _load_model():
    """加载 BGE-M3 模型（首次调用时加载，之后复用全局变量）。"""
    global _embed_model
    if _embed_model is None:
        print("[RAG] 正在加载 BGE-M3 模型（首次约 10-20 秒）...")
        if not os.path.exists(MODEL_PATH):
            print(f"[RAG] 错误：模型不存在 {MODEL_PATH}")
            sys.exit(1)
        _embed_model = BGEM3FlagModel(MODEL_PATH, use_fp16=False, device="cpu")
        print("[RAG] 模型加载完成")


def _chunk_text(text: str, chunk_size: int = 200, overlap: int = 40) -> list:
    """
    将长文本切分为适合向量检索的小块。
    切分策略：按空行分段 → 按中文标点切句子 → 合并到目标大小 + 重叠。
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    sentences = []
    for para in paragraphs:
        para = para.replace("\n", " ")
        for sep in ["。", "！", "？"]:
            para = para.replace(sep, sep + "<SPLIT>")
        for s in para.split("<SPLIT>"):
            s = s.strip()
            if s:
                sentences.append(s)

    chunks = []
    current = ""
    for s in sentences:
        if len(current) + len(s) <= chunk_size:
            current += s
        else:
            if current.strip():
                chunks.append(current.strip())
            current = (current[-overlap:] + s) if len(current) > overlap else s
    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if len(c) >= 20]


def _load_documents():
    """读取 product_manual/ 下所有 .txt，分块后向量化入库。"""
    global _collection

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        chroma_client.delete_collection("product_manual")
    except Exception:
        pass
    _collection = chroma_client.get_or_create_collection("product_manual")

    files = [f for f in os.listdir(MANUAL_DIR) if f.endswith(".txt")]
    if not files:
        print("[RAG] 警告：product_manual/ 目录下没有 .txt 文件")
        return

    all_chunks  = []
    all_sources = []

    for filename in files:
        filepath = os.path.join(MANUAL_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = _chunk_text(text)
        for c in chunks:
            all_chunks.append(c)
            all_sources.append(filename)

    if not all_chunks:
        print("[RAG] 警告：没有有效的文本块")
        return

    embeddings = _embed_model.encode(all_chunks)["dense_vecs"]
    ids = [f"c{i}" for i in range(len(all_chunks))]
    metas = [{"source": s} for s in all_sources]

    _collection.add(
        documents=all_chunks,
        embeddings=embeddings.tolist(),
        ids=ids,
        metadatas=metas,
    )
    print(f"[RAG] 知识库就绪：{len(files)} 个文件 → {len(all_chunks)} 个文本块")


def init_rag():
    """启动时调用一次：加载模型 + 建立向量库。"""
    global _ready
    _load_model()
    _load_documents()
    _ready = True
    print("[RAG] 初始化完成")


def search(query: str, top_k: int = 3) -> str:
    """
    语义检索 —— 输入问题，返回 Top-K 片段拼接文本。

    参数:
        query (str): 用户提问
        top_k (int): 返回片段数

    返回:
        str: 拼接后的检索结果；空字符串表示未找到
    """
    if not _ready:
        init_rag()

    q_vec = _embed_model.encode([query])["dense_vecs"][0]
    results = _collection.query(query_embeddings=[q_vec.tolist()], n_results=top_k)

    docs      = results.get("documents", [[]])[0]
    metas     = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not docs:
        return ""

    parts = []
    for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
        source = meta.get("source", "未知") if meta else "未知"
        parts.append(f"[来源:{source}，距离{dist:.3f}] {doc}")

    return "\n\n".join(parts)
