"""
Buffer Memory —— 滑动窗口记忆管理
====================================
功能：
  1. 只保留最近 max_turns 轮对话，超出自动丢弃
  2. 提供实时面板 HTML 展示当前记忆状态
  3. 全局单例，整个项目共享一个记忆实例

核心机制：history = history[-max_turns:]（Python 切片保底）
"""
from typing import List, Tuple


class BufferMemory:
    """
    滑动窗口记忆。

    参数:
        max_turns (int): 最多保留的对话轮数（默认 5）
    """

    def __init__(self, max_turns: int = 5):
        self.max_turns = max_turns
        self.history: List[Tuple[str, str]] = []
        self.discarded_count: int = 0

    def add(self, user_msg: str, ai_msg: str):
        """新增一轮对话。超过窗口自动丢弃最旧的。"""
        self.history.append((user_msg, ai_msg))
        if len(self.history) > self.max_turns:
            self.discarded_count += 1
            self.history = self.history[-self.max_turns:]

    def clear(self):
        """清空所有记忆。"""
        self.history = []
        self.discarded_count = 0

    def get_messages(self, system_prompt: dict) -> list:
        """
        将记忆窗口转为 LLM 可用的 messages 数组。

        参数:
            system_prompt (dict): {"role":"system","content":"..."}
        返回:
            [system_prompt, user1, assistant1, user2, assistant2, ...]
        """
        messages = [system_prompt]
        for user_msg, ai_msg in self.history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": ai_msg})
        return messages

    def get_panel_html(self) -> str:
        """生成右侧记忆面板 HTML——展示当前窗口内容。"""
        total = len(self.history)
        if total == 0:
            return (
                "<div style='padding:20px;text-align:center;color:#999;font-size:13px;'>"
                "暂无对话记录<br>发送第一条消息后这里会显示记忆窗口"
                "</div>"
            )

        pct = total / self.max_turns * 100
        bar_color = (
            "#52c41a" if pct < 60 else
            "#faad14" if pct < 100 else
            "#ff4d4f"
        )

        lines = [
            f"<div style='margin-bottom:8px;font-size:12px;color:#666;'>"
            f"记忆窗口：<b>{total}</b> / <b>{self.max_turns}</b> 轮"
        ]
        if self.discarded_count > 0:
            lines.append(
                f" &nbsp;|&nbsp; 已丢弃 <b style='color:#ff4d4f;'>{self.discarded_count}</b> 轮"
            )
        lines.append("</div>")

        lines.append(
            f"<div style='background:#eee;border-radius:6px;height:10px;"
            f"overflow:hidden;margin-bottom:10px;'>"
            f"<div style='background:{bar_color};height:100%;width:{pct}%;"
            f"border-radius:6px;transition:width 0.3s;'></div>"
            f"</div>"
        )

        for i, (user_msg, ai_msg) in enumerate(self.history):
            global_round = self.discarded_count + i + 1
            lines.append(
                f"<div style='background:#f7f7f7;border-radius:6px;padding:8px 10px;"
                f"margin-bottom:6px;'>"
                f"<div style='font-size:11px;color:#aaa;margin-bottom:3px;'>"
                f"第 {global_round} 轮</div>"
                f"<div style='font-size:12px;color:#333;margin-bottom:2px;'>"
                f"<b>Q:</b> {user_msg[:50]}{'...' if len(user_msg) > 50 else ''}</div>"
                f"<div style='font-size:12px;color:#888;'>"
                f"<b>A:</b> {ai_msg[:50]}{'...' if len(ai_msg) > 50 else ''}</div>"
                f"</div>"
            )

        if self.discarded_count > 0:
            lines.append(
                f"<div style='background:#fff7e6;border:1px solid #ffd591;"
                f"border-radius:6px;padding:8px 10px;font-size:11px;color:#ad6800;"
                f"margin-top:6px;'>"
                f"已丢弃 {self.discarded_count} 轮对话（超出 {self.max_turns} 轮窗口限制）。"
                f"<br>问关于它们的内容，AI 无法回忆。"
                f"</div>"
            )

        return "\n".join(lines)


# 全局单例
memory = BufferMemory(max_turns=5)
