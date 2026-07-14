# -*- coding: utf-8 -*-
"""
采集来源健康检查 - 检测各采集源网站是否可访问。
使用 requests 发送 HEAD/GET 请求，根据 HTTP 状态码和响应时间判断可用性。
"""
import time
import requests

# 各采集来源的检测配置
# url:     检测地址（与 get_*.py 中实际访问的入口页一致）
# name:    来源中文名
# method:  请求方法（部分网站不支持 HEAD，用 GET）
SOURCES = [
    {
        "key":  "gov",
        "name": "苏州市政府采购-招标公告",
        "url":  "https://czju.suzhou.gov.cn/zfcg/html/main/index.shtml",
        "method": "GET",
    },
    {
        "key":  "gov2",
        "name": "苏州市政府采购-采购意向",
        "url":  "https://czju.suzhou.gov.cn/zfcg/html/channel/cgyxgkForFirst.shtml",
        "method": "GET",
    },
    {
        "key":  "jc",
        "name": "金采平台公告",
        "url":  "http://www.cfcpn.com/jcw/sys/index/goUrl?url=modules/sys/login/list&column=cggg",
        "method": "GET",
    },
    {
        "key":  "public",
        "name": "苏州公共资源交易",
        "url":  "http://szzyjy.com.cn:8086/jyxx/tradeInfo.html",
        "method": "GET",
    },
    {
        "key":  "js",
        "name": "江苏省政府采购-招标公告",
        "url":  "http://www.ccgp-jiangsu.gov.cn/jiangsu/cggg_search.html?lmid=cggg&qh=notic_c4",
        "method": "GET",
    },
    {
        "key":  "js2",
        "name": "江苏省政府采购-采购意向",
        "url":  "http://www.ccgp-jiangsu.gov.cn/jiangsu/cggg_search.html?lmid=cgyx&qh=notic_c1",
        "method": "GET",
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TIMEOUT = 10   # 单个来源超时秒数


def check_source(source: dict) -> dict:
    """检测单个来源的可访问性"""
    key = source["key"]
    name = source["name"]
    url = source["url"]
    method = source.get("method", "GET")
    result = {
        "key": key,
        "name": name,
        "url": url,
        "status": "unknown",
        "status_code": None,
        "response_time": None,
        "error": None,
    }
    start = time.time()
    try:
        resp = requests.request(
            method, url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True
        )
        elapsed = round(time.time() - start, 2)
        result["status_code"] = resp.status_code
        result["response_time"] = elapsed
        if resp.status_code < 400:
            result["status"] = "ok"
        else:
            result["status"] = "error"
            result["error"] = f"HTTP {resp.status_code}"
    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["error"] = f"请求超时（{TIMEOUT}s）"
    except requests.exceptions.ConnectionError as e:
        result["status"] = "unreachable"
        result["error"] = "无法连接"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)[:100]
    return result


def check_all_sources() -> dict:
    """检测所有采集来源，返回汇总结果"""
    results = []
    ok_count = 0
    for src in SOURCES:
        r = check_source(src)
        results.append(r)
        if r["status"] == "ok":
            ok_count += 1
    return {
        "total": len(results),
        "ok": ok_count,
        "failed": len(results) - ok_count,
        "sources": results,
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
