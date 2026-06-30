"""
LLM 客户端封装 —— 智谱 API 统一调用入口
============================================
功能：
  1. 加载 .env 中的 API Key（硬编码绝对路径）
  2. 全局单例 ZhipuAI 客户端
  3. chat()      —— 非流式：Agent 决策用（需要完整 JSON）
  4. chat_stream() —— 流式：最终回答用（打字机效果）

设计要点：
  - 全局单例：_client 在模块加载时创建一次，所有引用方共享
  - 非流式用于 Agent 决策（需要完整 JSON 判断）
  - 流式用于最终回答（逐字展示，用户体验好）
"""
import os
from dotenv import load_dotenv
from zhipuai import ZhipuAI


# ==================== 加载 API Key ====================
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(project_root, ".env"))
_api_key = os.getenv("ZHIPU_API_KEY")

if not _api_key or _api_key == "your_api_key_here":
    raise ValueError(
        "请先在 .env 中配置 ZHIPU_API_KEY\n"
        f"打开 {os.path.join(project_root, '.env')}\n"
        "将 your_api_key_here 替换为你的真实 API Key"
    )


# ==================== 全局单例客户端 ====================
_client = ZhipuAI(api_key=_api_key)


# ==================== 非流式对话（Agent 决策用） ====================
def chat(messages: list, temperature: float = 0.3) -> str:
    """
    非流式对话 —— 发送完整 messages，等待 LLM 返回完整回答。

    为什么 Agent 决策必须用非流式？
      → Agent 需要看到 LLM 的完整输出才能判断有没有「Final Answer」或「Action」
      → 流式输出是逐 token 返回的，无法一次性解析 JSON

    参数:
        messages (list): [{"role":"system"/"user"/"assistant","content":"..."}, ...]
        temperature (float): 0~1，Agent 决策设 0.1 确保 JSON 格式稳定

    返回:
        str: LLM 的完整回答文本
    """
    response = _client.chat.completions.create(
        model="glm-4-flash",
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


# ==================== 流式对话（最终回答用） ====================
def chat_stream(messages: list, temperature: float = 0.3):
    """
    流式对话 —— 逐 token 返回，实现打字机效果。

    为什么最终回答用流式？
      → 用户不用等 3 秒看一大段文字
      → 逐字出现的打字机效果体验好，像真人回复

    参数:
        messages (list): 同上
        temperature (float): 0~1，回答设 0.5 自然但不发散

    Yields:
        str: 每次 yield 一个 delta.content 片段
    """
    stream = _client.chat.completions.create(
        model="glm-4-flash",
        messages=messages,
        stream=True,
        temperature=temperature,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
