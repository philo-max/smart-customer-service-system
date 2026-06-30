"""
Guardrails 安全模块 —— 输入/输出双层安全护栏
================================================
功能：
  InputGuard  —— 输入层：拦截恶意 Prompt 注入
  OutputGuard —— 输出层：屏蔽敏感信息泄露

比喻：机场安检——进门查违禁品，出门查夹带。
"""
import re


class InputGuard:
    """
    输入护栏：在 LLM 处理用户输入之前检查安全性。

    三层检查：
      1. 黑名单正则 — 匹配「忽略指令」「假装你是」等已知攻击模式
      2. 长度限制   — 拒绝超长输入（>5000 字符）
      3. 代码注入   — 拦截 DROP TABLE、<script>、eval( 等
    """

    BLOCKED_PATTERNS = [
        (r"忽略.*指令", "指令覆盖攻击"),
        (r"忘记.*规则", "规则绕过攻击"),
        (r"假装你是", "角色伪装攻击"),
        (r"系统.*提示词", "提示词泄露攻击"),
        (r"DAN\b", "DAN 越狱攻击"),
        (r"jailbreak", "越狱关键词"),
        (r"输出.*密码", "密码窃取攻击"),
        (r"你是开发者", "开发者身份伪装"),
        (r"developer mode", "开发者模式诱导"),
    ]

    MAX_INPUT_LENGTH = 5000

    DANGEROUS_CHARS = [
        "DROP TABLE", "<script>", "eval(", "exec(",
        "__import__", "os.system",
    ]

    @classmethod
    def check(cls, user_input: str) -> tuple:
        """
        检查用户输入的安全性。
        返回: (is_safe: bool, reason: str)
        """
        if len(user_input) > cls.MAX_INPUT_LENGTH:
            return False, f"输入过长（{len(user_input)} 字符），超过 {cls.MAX_INPUT_LENGTH} 字符限制"

        for pattern, desc in cls.BLOCKED_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                return False, f"检测到恶意输入（{desc}）"

        user_lower = user_input.lower()
        for dc in cls.DANGEROUS_CHARS:
            if dc.lower() in user_lower:
                return False, f"检测到代码注入尝试：包含「{dc}」"

        return True, "OK"


class OutputGuard:
    """
    输出护栏：在 LLM 生成回答后检查输出内容。

    三层检查：
      1. 敏感信息 — 拦截 API Key、银行卡号、手机号、身份证
      2. 不安全内容 — 拦截暴力、违法、危险内容关键词
      3. 输出长度 — 拒绝超长输出（>10000 字符）
    """

    SENSITIVE_PATTERNS = [
        (r"\b[A-Za-z0-9]{32}\.[A-Za-z0-9]{16,}\b", "疑似 智谱 API Key/Token"),
        (r"\b\d{16,19}\b", "疑似银行卡号"),
        (r"\b1[3-9]\d{9}\b", "疑似手机号"),
        (r"\b\d{17}[\dXx]\b", "疑似身份证号"),
        (r"password\s*[:=]\s*\S+", "疑似密码明文泄露"),
        (r"\bsk-[A-Za-z0-9]{32,}\b", "疑似 OpenAI API Key"),
    ]

    UNSAFE_CONTENT = [
        "制作炸弹", "病毒制作", "黑客教程",
        "非法入侵", "毒品制作", "武器制造",
    ]

    MAX_OUTPUT_LENGTH = 10000

    @classmethod
    def check(cls, llm_output: str) -> tuple:
        """
        检查 LLM 输出的安全性。
        返回: (is_safe: bool, reason: str)
        """
        if len(llm_output) > cls.MAX_OUTPUT_LENGTH:
            return False, f"输出过长（{len(llm_output)} 字符）"

        for pattern, desc in cls.SENSITIVE_PATTERNS:
            match = re.search(pattern, llm_output, re.IGNORECASE)
            if match:
                return False, f"输出包含{desc}（已屏蔽）"

        for keyword in cls.UNSAFE_CONTENT:
            if keyword in llm_output:
                return False, f"输出包含不安全内容（关键词：「{keyword}」）"

        return True, "OK"
