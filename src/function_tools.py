"""
Function Calling 工具模块 —— 业务操作接口
=============================================
功能：三个业务工具，模拟企业 CRM 系统。
  1. check_order()      —— 查询订单状态和详情
  2. request_refund()   —— 申请退款（含状态校验）
  3. transfer_to_human() —— 转接人工客服
"""
from typing import Optional


# ==================== 模拟订单数据库 ====================
MOCK_ORDERS = {
    "ORD-2024-001": {
        "status": "已发货", "product": "APOLLO-RK3588 旗舰版",
        "amount": 3980, "date": "2024-06-15",
    },
    "ORD-2024-002": {
        "status": "待发货", "product": "MERCURY-Linux 标准平台",
        "amount": 8980, "date": "2024-06-18",
    },
    "ORD-2024-003": {
        "status": "已完成", "product": "APOLLO-RK3568 标准版",
        "amount": 1980, "date": "2024-05-20",
    },
    "ORD-2024-004": {
        "status": "已退款", "product": "散热片套件",
        "amount": 120, "date": "2024-06-01",
    },
    "ORD-2024-005": {
        "status": "已发货", "product": "MERCURY-FPGA 混合平台",
        "amount": 12800, "date": "2024-06-20",
    },
}

STATUS_DESC = {
    "已发货": "物流运输中，预计 3-5 个工作日送达",
    "待发货": "订单已确认，仓库正在备货，预计 1-2 个工作日发货",
    "已完成": "已签收，订单完成",
    "已退款": "退款已处理，款项已退回原支付方式",
}


# ==================== 工具 1：查询订单 ====================
def check_order(order_id: str) -> str:
    """查询订单状态和详细信息。"""
    order_id = order_id.strip().upper()
    order = MOCK_ORDERS.get(order_id)

    if not order:
        available = ", ".join(MOCK_ORDERS.keys())
        return (
            f"未找到订单 {order_id}。\n"
            f"系统中有以下订单：{available}\n"
            f"请核对订单号后重试。"
        )

    desc = STATUS_DESC.get(order["status"], order["status"])

    return (
        f"订单 {order_id} 详细信息：\n"
        f"  ─────────────────\n"
        f"  商品：{order['product']}\n"
        f"  金额：￥{order['amount']:,}\n"
        f"  日期：{order['date']}\n"
        f"  状态：{order['status']}\n"
        f"  说明：{desc}\n"
        f"  ─────────────────"
    )


# ==================== 工具 2：申请退款 ====================
def request_refund(order_id: str, reason: str = "用户申请退款") -> str:
    """为用户申请退款。含状态校验：已退款拒绝重复、已完成需人工审核。"""
    order_id = order_id.strip().upper()
    order = MOCK_ORDERS.get(order_id)

    if not order:
        available = ", ".join(MOCK_ORDERS.keys())
        return (
            f"未找到订单 {order_id}，无法处理退款。\n"
            f"可用订单：{available}"
        )

    if order["status"] == "已退款":
        return f"订单 {order_id} 已经退款完成，无需重复操作。"

    if order["status"] == "已完成":
        return (
            f"订单 {order_id} 已签收超过 7 天，退款需人工审核。\n"
            f"已将申请转交客服部门处理，预计 1 个工作日内回复。\n"
            f"紧急可拨打客服电话：0755-8888-6666"
        )

    return (
        f"退款申请已提交：\n"
        f"  ─────────────────\n"
        f"  订单号：{order_id}\n"
        f"  商品：{order['product']}\n"
        f"  金额：￥{order['amount']:,}\n"
        f"  退款原因：{reason}\n"
        f"  预计到账：3-5 个工作日\n"
        f"  ─────────────────\n"
        f"退款将原路返回至支付账户。"
    )


# ==================== 工具 3：转人工客服 ====================
def transfer_to_human(reason: str = "用户请求人工服务") -> str:
    """转接人工客服。"""
    return (
        f"正在为您转接人工客服，请稍候...\n"
        f"  ─────────────────\n"
        f"  转接原因：{reason}\n"
        f"  预计等待：约 1 分钟\n"
        f"  在线时间：工作日 9:00-18:00\n"
        f"  客服电话：0755-8888-6666\n"
        f"  ─────────────────\n"
        f"温馨提示：非工作时间可留言，客服将在下一个工作日与您联系。"
    )


# ==================== Function Calling 工具注册表 ====================
FC_TOOLS = {
    "check_order": {
        "function": check_order,
        "description": "查询指定订单的状态、商品、金额、日期等详细信息",
        "parameters": {"order_id": "订单编号，如 ORD-2024-001"},
    },
    "request_refund": {
        "function": request_refund,
        "description": "为用户申请退款，自动校验退款条件",
        "parameters": {
            "order_id": "订单编号",
            "reason": "退款原因（可选，如「不想要了」「发错货」）",
        },
    },
    "transfer_to_human": {
        "function": transfer_to_human,
        "description": "将当前对话转接给人工客服处理",
        "parameters": {"reason": "转接原因（可选）"},
    },
}
