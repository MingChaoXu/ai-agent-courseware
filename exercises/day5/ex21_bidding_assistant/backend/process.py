import os
import json
import time
import sys
import re
import threading

import requests

# SiliconFlow API 配置（从环境变量读取，部署时在 systemd 或 .env 中配置）
SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")
SILICONFLOW_API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-v4-flash"  # SiliconFlow 支持的模型


# ================================================================== #
#  熔断器：连续失败超阈值后快速失败，避免长时间无效重试
# ================================================================== #
class CircuitBreaker:
    """简单的熔断器。
    - 连续失败达到 failure_threshold 后进入 OPEN 状态，直接快速失败
    - 等待 cooldown 秒后进入 HALF_OPEN，允许一次试探
    - 试探成功则 CLOSED，失败则继续 OPEN
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, failure_threshold: int = 5, cooldown: float = 60.0):
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self._state = self.CLOSED
        self._failures = 0
        self._opened_at = 0.0
        self._lock = threading.Lock()

    @property
    def state(self):
        with self._lock:
            if self._state == self.OPEN:
                # 冷却期过则进入半开
                if time.time() - self._opened_at >= self.cooldown:
                    self._state = self.HALF_OPEN
            return self._state

    def allow(self) -> bool:
        """是否允许调用。CLOSED/HALF_OPEN 允许，OPEN 拒绝。"""
        return self.state in (self.CLOSED, self.HALF_OPEN)

    def record_success(self):
        with self._lock:
            self._failures = 0
            self._state = self.CLOSED

    def record_failure(self):
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._state = self.OPEN
                self._opened_at = time.time()

    def reset(self):
        with self._lock:
            self._failures = 0
            self._state = self.CLOSED
            self._opened_at = 0.0


# 全局熔断器实例：连续 5 次失败后熔断 60 秒
_ai_breaker = CircuitBreaker(failure_threshold=5, cooldown=60.0)


def reset_ai_breaker():
    """重置熔断器（手动恢复用）。"""
    _ai_breaker.reset()


def ai_breaker_state() -> str:
    return _ai_breaker.state


def call_siliconflow( prompt, system_prompt="你是一个数据提取助手，只返回要求的 JSON 格式。", max_retries=3,
                     retry_delay=2.0):
    """
    调用 SiliconFlow API 发送请求

    Args:
        prompt (str): 用户提示词
        system_prompt (str): 系统提示词
        max_retries (int): 最大重试次数
        retry_delay (float): 重试延迟（秒）

    Returns:
        str: API 返回的完整文本，失败返回 None
    """
    # 熔断器检查：OPEN 状态直接快速失败
    if not _ai_breaker.allow():
        print("  [熔断器] AI 接口已熔断，跳过本次调用（请稍后重试或手动重置）")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    }

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(SILICONFLOW_API_URL, headers=headers, json=payload, timeout=120)
            response.raise_for_status()

            result = response.json()

            # 提取回复内容（不打印完整返回，避免日志冗长）
            full_text = ""
            if "content" in result and isinstance(result["content"], list):
                for content_item in result["content"]:
                    if isinstance(content_item, dict) and content_item.get("type") == "text":
                        if "text" in content_item:
                            full_text = content_item["text"]
                            break
            if not full_text and "choices" in result and len(result["choices"]) > 0:
                full_text = result["choices"][0].get("message", {}).get("content", "")
            # 成功：重置熔断器
            _ai_breaker.record_success()
            return full_text

        except Exception as e:
            last_error = e
            wait = retry_delay * (2 ** (attempt - 1))  # 指数退避：2s → 4s → 8s
            if attempt < max_retries:
                print(f"  [第{attempt}次失败] {e}，{wait:.0f}s 后重试...")
                time.sleep(wait)
            else:
                print(f"  [第{attempt}次失败] {e}，已达最大重试次数。")

    # 全部重试失败：记录熔断器失败
    _ai_breaker.record_failure()
    return None


def extract_info_with_siliconflow(item, max_retries: int = 3, retry_delay: float = 2.0):
    """
    调用 SiliconFlow 模型提取五个字段：amount, is_it, public_due, result_due, tenderer
    返回包含这五个字段的字典，若全部重试均失败则返回 None。

    :param item:         包含 title / date / content 的公告字典
    :param max_retries:  最大重试次数（含首次，默认 3）
    :param retry_delay:  首次重试等待秒数，后续指数退避（×2）
    """
    prompt = f"""请从以下政府采购公告信息中提取指定字段，并以 JSON 格式返回。

标题：{item['title']}
发布日期：{item['date']}
公告全文：{item['content']}

要求：
1. 项目金额（从公告全文内容中提取预算金额或最高限价，单位保留"万元"，如"385.000000万元"）
2. 信息化与否（根据标题和正文内容判断：如果包含"信息化"、"软件"、"系统"、"平台"、"数字化"、"智能"等关键词，则返回"是"，否则返回"否"）
3. 公告期限（从公告全文内容中提取公告期限，保留文字描述，如"5个工作日"）
4. 开标日期（从公告全文内容中提取开标日期，保留到日，如"2025-10-31"）
5. 招标人（从公告全文内容中提取招标人/采购人/招标单位/采购单位，需提取完整的公司名称，如"XX市人民政府采购中心"）

请严格按照以下格式返回 JSON，不要包含任何额外文字或解释：
{{
    "amount": "金额",
    "is_it": "是/否",
    "public_due": "公告期限",
    "result_due": "开标日期",
    "tenderer": "招标人完整名称"
}}
"""

    system_prompt = "你是一个数据提取助手，只返回要求的 JSON 格式。"

    full_text = call_siliconflow(prompt, system_prompt, max_retries, retry_delay)

    if full_text is None:
        return None

    try:
        # 尝试从回复中提取 JSON
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', full_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = full_text.strip()

        extracted = json.loads(json_str)
        result = {
            "amount": extracted.get("amount"),
            "is_it": extracted.get("is_it"),
            "public_due": extracted.get("public_due"),
            "result_due": extracted.get("result_due"),
            "tenderer": extracted.get("tenderer"),
        }
        # 只输出提取到的字段，不输出完整返回内容
        print(f"    → 金额: {result['amount']} | 信息化: {result['is_it']} | "
              f"公告期限: {result['public_due']} | 开标日期: {result['result_due']} | "
              f"招标人: {result['tenderer']}")
        return result
    except Exception as e:
        print(f"  JSON 解析失败: {e}")
        return None

def main(input_file="recent_bulletins.json", output_file="extracted_info.json"):
    # 读取本地 JSON 文件
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            json_list = json.load(f)
    except FileNotFoundError:
        print(f"错误：文件 {input_file} 未找到，请确保文件存在。")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误：JSON 解析失败 - {e}")
        sys.exit(1)

    if not isinstance(json_list, list):
        print("错误：输入文件应包含一个 JSON 数组。")
        sys.exit(1)

    results = []
    for idx, item in enumerate(json_list):
        print(f"正在处理第 {idx+1} 条...")
        extracted = extract_info_with_siliconflow(item)
        if extracted:
            results.append({
                "title": item["title"],
                "date": item["date"],
                "url": item["url"],          # 保留原始 URL
                "content": item["content"],  # 保留原始全文
                "amount": extracted["amount"],
                "is_it": extracted["is_it"],
                "public_due": extracted["public_due"],
                "result_due": extracted["result_due"],
                "tenderer": extracted["tenderer"]
            })
        else:
            # 提取失败，保留原始标题、日期、url、content，其他字段设为 None
            results.append({
                "title": item["title"],
                "date": item["date"],
                "url": item["url"],
                "content": item["content"],
                "amount": None,
                "is_it": None,
                "public_due": None,
                "result_due": None,
                "tenderer": None
            })
        time.sleep(1)

    # 输出结果到控制台
    print("提取结果：")
    print(json.dumps(results, ensure_ascii=False, indent=2))

    # 保存到文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"处理完成，结果已保存到 {output_file}")

if __name__ == "__main__":
    input_file = "public.json"
    output_file = "output.json"
    main(input_file, output_file)
