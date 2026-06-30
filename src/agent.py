"""
Agent 调度中心 —— 智能客服的核心大脑
========================================
功能：
  1. ReAct 循环：Thought → Action → Observation → Final Answer
  2. 整合 7 个工具：RAG + MCP(3个) + Function Calling(3个)
  3. 自动判断：需要什么工具、什么时候用、什么时候完成
  4. 安全防护：InputGuard + OutputGuard 贯穿始终
"""
import json
import re

from .llm_client import chat as llm_chat
from .rag_retriever import search as rag_search
from .mcp_tools import MCP_TOOLS
from .function_tools import FC_TOOLS
from .guardrails import InputGuard, OutputGuard


# ==================== 全局工具注册表 ====================
ALL_TOOLS = {}

ALL_TOOLS["rag_search"] = {
    "function": rag_search,
    "description": "在 RAG 产品知识库中搜索，获取产品规格、功能、价格等信息。适用于产品咨询类问题。",
    "parameters": {"query": "搜索关键词，如「RK3588 价格」"},
}

ALL_TOOLS.update({f"mcp_{name}": info for name, info in MCP_TOOLS.items()})
ALL_TOOLS.update(FC_TOOLS)


# ==================== 构建工具描述 Prompt ====================
def _build_tools_prompt() -> str:
    """动态生成工具列表描述，嵌入 Agent System Prompt。"""
    lines = ["## 可用工具清单"]
    for name, info in ALL_TOOLS.items():
        params = info.get("parameters", {})
        if params:
            param_desc = "、".join([f"{k}（{v}）" for k, v in params.items()])
            lines.append(f"- **{name}**: {info['description']}")
            lines.append(f"  参数: {param_desc}")
        else:
            lines.append(f"- **{name}**: {info['description']}（无参数）")
    return "\n".join(lines)


# ==================== Agent System Prompt ====================
AGENT_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "你是鸿芯智谷（HongXin ZhiGu）的智能客服助手「小芯」。\n\n"
        + _build_tools_prompt() + "\n\n"
        "## ReAct 工作格式（必须严格遵循）：\n\n"
        "情况1：不需要工具（问候、感谢、简单闲聊）\n"
        "  直接输出：Final Answer: [你的回答]\n\n"
        "情况2：需要工具（产品咨询、查订单、退款、读文件等）\n"
        "  第一步：Thought: [分析当前任务，说明为什么需要这个工具]\n"
        "  第二步：Action: {\"tool\":\"工具名\",\"params\":{\"参数名\":\"参数值\"}}\n"
        "  收到 Observation 后，判断是否还需要继续：\n"
        "    - 需要更多信息 → 继续 Thought → Action\n"
        "    - 信息足够了   → Final Answer: [综合所有信息给用户的回答]\n\n"
        "## 决策规则（重要）：\n"
        "- 问产品规格、功能、价格、参数 → 用 rag_search\n"
        "- 问订单状态或物流 → 用 check_order\n"
        "- 要求退款 → 用 request_refund\n"
        "- 要求人工客服 → 用 transfer_to_human\n"
        "- 问产品目录、文件列表 → 用 mcp_list_products\n"
        "- 要求查看产品文件内容 → 用 mcp_get_product\n"
        "- 在产品中搜索 → 用 mcp_search_catalog\n"
        "- 问候、自我介绍、感谢 → 直接 Final Answer，不调工具\n\n"
        "## 回答风格：\n"
        "- 专业但不生硬，像有经验的客服人员\n"
        "- 善用列表和分段，让信息一目了然\n"
        "- 提及产品时标注价格和型号\n"
        "- 结束时可以主动问「还有什么可以帮您的吗？」"
    ),
}

MAX_LOOP = 5


def agent_chat(message: str, history: list):
    """
    Agent 对话入口（流式生成器）。

    参数:
        message (str): 用户当前输入
        history (list): 对话历史 [{"role":"user"/"assistant","content":"..."}, ...]

    Yields:
        str: 决策过程日志 + 最终回答
    """
    if not message.strip():
        yield "请输入你的问题，我来帮你解答。"
        return

    # ---- 第0层：输入护栏 ----
    safe, reason = InputGuard.check(message)
    if not safe:
        yield f"> 输入被安全护栏拦截：{reason}\n\n请使用正常的提问方式，我会尽力帮您解决问题。"
        return

    # ---- 构建初始 messages ----
    messages = [AGENT_SYSTEM_PROMPT]
    for h in history:
        if isinstance(h, dict):
            messages.append({"role": h["role"], "content": h["content"]})
        else:
            messages.append({"role": "user", "content": str(h[0])})
            if len(h) > 1 and h[1]:
                messages.append({"role": "assistant", "content": str(h[1])})

    messages.append({"role": "user", "content": message})

    # ---- ReAct 决策循环 ----
    agent_log = []

    for loop_idx in range(MAX_LOOP):
        # 1. LLM 决策
        try:
            agent_text = llm_chat(messages, temperature=0.1)
        except Exception as e:
            yield f"> 系统错误：LLM 调用失败\n> {e}"
            return

        agent_log.append(f"\n**第 {loop_idx+1} 轮决策**\n{agent_text}")

        # 2. 检查是否完成
        if "Final Answer:" in agent_text:
            final = agent_text.split("Final Answer:")[-1].strip()

            safe, reason = OutputGuard.check(final)
            if not safe:
                final = f"> 回答被安全护栏拦截：{reason}\n\n为保障信息安全，此回复已被自动屏蔽。"

            yield "".join(agent_log) + "\n\n---\n**最终回答**\n\n" + final
            return

        # 3. 检查是否需要工具
        if "Action:" in agent_text:
            start = agent_text.find('{')
            end = agent_text.rfind('}')
            if start == -1 or end == -1 or end < start:
                messages.append({"role": "assistant", "content": agent_text})
                messages.append({"role": "user", "content": "请用标准 JSON 格式输出 Action，形如 Action: {...}"})
                continue

            try:
                action = json.loads(agent_text[start:end+1])
                tool_name = action.get("tool", "")
                params    = action.get("params", {})

                if tool_name in ALL_TOOLS:
                    func = ALL_TOOLS[tool_name]["function"]
                    result = func(**params) if params else func()
                    obs = f"Observation: {result}"
                else:
                    obs = f"Observation: 未知工具 '{tool_name}'。可用工具：{', '.join(ALL_TOOLS.keys())}"

                agent_log.append(f"\n{obs}")
                messages.append({"role": "assistant", "content": agent_text})
                messages.append({"role": "user", "content": obs})

            except (json.JSONDecodeError, TypeError) as e:
                agent_log.append(f"\nObservation: 工具调用失败 - {e}")
                messages.append({"role": "assistant", "content": agent_text})
                messages.append({"role": "user", "content": f"执行失败：{e}，请重新输出"})
        else:
            yield "".join(agent_log)
            return

    # MAX_LOOP 兜底
    agent_log.append(f"\n> 已达到最大决策轮数（{MAX_LOOP}），正在生成最终回答...")
    try:
        final = llm_chat(
            messages + [{"role": "user", "content": "基于以上信息给出最终回答。"}],
            temperature=0.5,
        )
        safe, reason = OutputGuard.check(final)
        if not safe:
            final = f"> 回答被安全护栏拦截：{reason}"
        yield "".join(agent_log) + "\n\n" + final
    except Exception:
        yield "".join(agent_log) + "\n\n抱歉，处理超时。请重新描述您的问题。"
