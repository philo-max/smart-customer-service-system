"""
智能客服系统 - 主程序
======================
功能：Gradio 前端界面 + 全部模块集成。
      - 左侧：聊天界面（ChatInterface）
      - 右侧：Memory 记忆面板（HTML 面板）

运行方式：python app.py → 浏览器打开 http://127.0.0.1:7860
"""
import gradio as gr

from src.rag_retriever import init_rag
from src.agent import agent_chat
from src.memory import memory


# ==================== 启动时初始化 RAG ====================
print("=" * 56)
print("  鸿芯智谷 · 智能客服系统 启动中...")
print("=" * 56)
init_rag()
print("  系统就绪。浏览器访问 http://127.0.0.1:7860")
print()


# ==================== 对话响应函数 ====================
def respond(message: str, history: list):
    """
    Gradio ChatInterface 调用的对话响应函数。

    参数:
        message (str): 用户当前输入
        history (list): [{"role":"user","content":"..."}, ...]

    Yields:
        str: 流式回答（Agent 决策过程 + 最终回复）
    """
    last_response = ""
    for chunk in agent_chat(message, history):
        last_response = chunk
        yield chunk

    if last_response:
        memory.add(message, last_response)


# ==================== 界面主题 ====================
custom_theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="blue",
    neutral_hue="gray",
).set(
    body_background_fill="*neutral_50",
    block_background_fill="white",
    block_border_width="0px",
    block_shadow="0 1px 3px rgba(0,0,0,0.06)",
    block_radius="14px",
    button_primary_background_fill="*primary_500",
    button_primary_background_fill_hover="*primary_600",
    button_border_width="0px",
    button_primary_text_color="white",
    button_medium_radius="10px",
    input_radius="10px",
    input_background_fill="*neutral_100",
    input_border_width="1.5px",
    input_border_color="*neutral_200",
    input_border_color_focus="*primary_400",
    input_shadow_focus="0 0 0 3px rgba(22,119,255,0.1)",
)


# ==================== 构建 Gradio 界面 ====================
with gr.Blocks(title="智能客服系统", theme=custom_theme) as demo:
    gr.Markdown(
        """
        # 鸿芯智谷 · 智能客服系统

        **9 模块集成**：Agent · RAG · MCP · Function Calling · Guardrails · Memory · LLM · Dify · Gradio
        ---
        """
    )

    with gr.Row():
        with gr.Column(scale=3, min_width=420):
            chatbot = gr.ChatInterface(
                fn=respond,
                chatbot=gr.Chatbot(
                    height=500,
                    layout="bubble",
                    placeholder="我是智能客服「小芯」，可以帮您：查产品 · 查订单 · 退款 · 转人工 · 读文件目录",
                ),
                textbox=gr.Textbox(
                    placeholder="输入您的问题，我会尽力帮您解决...",
                    container=False,
                    scale=7,
                ),
                title=None,
                description=None,
                examples=[
                    "APOLLO-RK3588 有哪些接口和价格？",
                    "帮我查一下订单 ORD-2024-001 的状态",
                    "我要退款，订单号 ORD-2024-002，原因是不想要了",
                    "列出所有产品目录文件",
                    "转人工客服",
                    "MERCURY-Linux 平台多少钱？适合什么场景？",
                ],
                cache_examples=False,
            )

        with gr.Column(scale=1, min_width=240):
            gr.Markdown("### 记忆窗口状态")
            memory_panel = gr.HTML(value=memory.get_panel_html(), every=3)

    gr.Markdown(
        """
        ---
        ### 系统能力总览

        | 能力 | 触发方式 | 示例问题 |
        |------|---------|---------|
        | 产品咨询 | 问产品规格、功能、价格 | 「RK3588 有多少个接口？」 |
        | 查订单 | 提供订单号 | 「查一下 ORD-2024-001」 |
        | 退款 | 要求退款 | 「我要退款 ORD-2024-002」 |
        | 产品目录 | 要求列出或搜索文件 | 「有哪些产品文件？」 |
        | 转人工 | 要求人工客服 | 「找人工客服」 |
        | 安全防护 | 输入恶意 Prompt 或敏感词 | 系统自动拦截 |
        """
    )


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
