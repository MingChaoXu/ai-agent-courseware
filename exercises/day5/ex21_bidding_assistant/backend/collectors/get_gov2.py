import time
import json
import os
import shutil
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# 目标网址
BASE_URL = "https://czju.suzhou.gov.cn/zfcg/html/channel/cgyxgkForFirst.shtml"
# 网站根域名，用于拼接相对链接
SITE_ROOT = "https://czju.suzhou.gov.cn/zfcg/"

# 请求头，模拟浏览器访问
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
}


def setup_driver(headless=True):
    """配置 Chrome 浏览器驱动"""
    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    # 显式指定 chromedriver 路径，避免 selenium-manager 联网检查
    chromedriver_path = (
        os.environ.get("CHROMEDRIVER_PATH")
        or shutil.which("chromedriver")
        or "/usr/local/bin/chromedriver"
    )
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def select_area_and_search(driver):
    """选择区域为'苏州市级'并点击搜索按钮"""
    area_select = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "areas"))
    )
    for option in area_select.find_elements(By.TAG_NAME, "option"):
        if option.get_attribute("value") == "苏州":
            option.click()
            break

    search_btn = driver.find_element(By.CSS_SELECTOR, "input.button[value='搜 索']")
    search_btn.click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#lis li"))
    )
    time.sleep(1)


def parse_date(date_str):
    """将列表页的日期字符串转换为 datetime 对象
    输入格式如 "[2026-03-30 ]" 或 "2026-03-30"
    """
    cleaned = date_str.strip("[] ").strip()
    return datetime.strptime(cleaned, "%Y-%m-%d")


def is_within_7_days(date_obj):
    """判断日期是否在最近7天内（含今天）"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    delta = today - date_obj
    return 0 <= delta.days <= 7


def get_page_items(driver):
    """获取当前页面的所有采购意向条目（标题、链接、日期），并过滤出7天内的条目
    返回 (items_keep, stop_flag)
    items_keep: 7天内的条目列表
    stop_flag: 如果当前页出现超出7天的条目（因为按时间倒序，后续条目更旧），则停止翻页
    """
    items_keep = []
    li_list = driver.find_elements(By.CSS_SELECTOR, "#lis li")
    for li in li_list:
        try:
            a_tag = li.find_element(By.CSS_SELECTOR, ".List_t a")
            title = a_tag.get_attribute("title") or a_tag.text.strip()
            relative_link = a_tag.get_attribute("href")
            full_link = urljoin(SITE_ROOT, relative_link)

            date_span = li.find_element(By.CSS_SELECTOR, ".L_date")
            date_str = date_span.text.strip()
            date_obj = parse_date(date_str)

            if is_within_7_days(date_obj):
                items_keep.append({
                    "title": title,
                    "url": full_link,
                    "date": date_str
                })
            else:
                # 因为列表按时间倒序排列，遇到第一条超出7天的条目，后续都会超出
                # 返回当前已收集的条目，并告知调用方停止翻页
                return items_keep, True
        except Exception as e:
            print(f"解析条目时出错: {e}")
            continue
    return items_keep, False


def go_to_next_page(driver):
    """点击下一页按钮，返回是否成功"""
    try:
        next_btn = driver.find_element(By.ID, "next")
        if "gray" in next_btn.get_attribute("style"):
            return False
        next_btn.click()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#lis li"))
        )
        time.sleep(1)
        return True
    except Exception as e:
        print(f"翻页失败: {e}")
        return False


def fetch_detail_content(url):
    """使用 requests 获取详情页内容，提取标题、发稿时间和正文文本
    返回字典: {"title": str, "publish_date": str, "content": str}
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # 提取标题
        title_elem = soup.select_one(".M_title, h1")
        title = title_elem.get_text(strip=True) if title_elem else ""

        # 提取发稿时间
        date_elem = soup.select_one(".date span")
        publish_date = date_elem.get_text(strip=True) if date_elem else ""

        # 提取正文内容（.Article 区域）
        article_elem = soup.select_one(".Article")
        if article_elem:
            # 获取纯文本，保留换行和表格文本
            content = article_elem.get_text(separator="\n", strip=True)
        else:
            content = ""

        return {
            "title": title,
            "publish_date": publish_date,
            "content": content
        }
    except Exception as e:
        print(f"获取详情页失败 {url}: {e}")
        return None


def run() -> tuple:
    """
    采集苏州市政府采购平台最近7天的「采购意向」公告。
    返回：(记录列表, 中间文件路径)，每条记录包含 title / url / date / content。
    中间文件带时间戳，供 pipeline 集成后删除。
    """
    driver = setup_driver(headless=True)
    try:
        print("[gov2] 正在打开采购意向页面...")
        driver.get(BASE_URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "areas"))
        )

        print("[gov2] 选择区域'苏州市级'并点击搜索...")
        select_area_and_search(driver)

        all_items = []
        current_page = 1

        while True:
            print(f"[gov2] 正在爬取第 {current_page} 页...")
            page_items, stop_flag = get_page_items(driver)
            print(f"[gov2]   当前页获取到 {len(page_items)} 条7天内记录")
            all_items.extend(page_items)

            if stop_flag:
                print("[gov2]   已遇到超出7天的条目，停止翻页。")
                break
            if not go_to_next_page(driver):
                print("[gov2] 无法继续翻页，结束。")
                break
            current_page += 1

        print(f"共找到 {len(all_items)} 条最近7天的记录")

        total = len(all_items)
        success_count = 0
        results = []
        for idx, item in enumerate(all_items, 1):
            print(f"({idx}/{total}) 正在抓取: {item['title']}")
            detail = fetch_detail_content(item["url"])
            if detail and detail.get("content"):
                results.append({
                    "title":   detail["title"] or item["title"],
                    "url":     item["url"],
                    "date":    item["date"],
                    "content": detail["content"],
                })
                success_count += 1
            else:
                # 提取失败也保留数据，content 为空
                results.append({
                    "title":   item["title"],
                    "url":     item["url"],
                    "date":    item["date"],
                    "content": "",
                })
            time.sleep(0.5)

        print(f"共获取 {total} 条，{success_count} 条正文部分提取成功")

        # 生成带时间戳的中间文件
        os.makedirs(DATA_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        intermediate_file = os.path.join(DATA_DIR, f"intermediate_gov2_{ts}.json")
        with open(intermediate_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"[gov2] 中间文件已保存: {intermediate_file}")

        return results, intermediate_file

    finally:
        driver.quit()


def main():
    driver = setup_driver(headless=True)
    try:
        print("正在打开目标页面...")
        driver.get(BASE_URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "areas"))
        )

        print("选择区域'苏州市级'并点击搜索...")
        select_area_and_search(driver)

        all_items = []       # 保存7天内的列表信息（含url）
        current_page = 1
        stop = False

        while not stop:
            print(f"正在爬取第 {current_page} 页...")
            page_items, stop_flag = get_page_items(driver)
            print(f"  当前页获取到 {len(page_items)} 条7天内的记录")
            all_items.extend(page_items)

            # 如果当前页出现了超出7天的条目，停止翻页
            if stop_flag:
                print("  已遇到超出7天的条目，停止翻页。")
                break

            # 尝试翻页
            if not go_to_next_page(driver):
                print("无法继续翻页，结束。")
                break
            current_page += 1

        print(f"共收集到 {len(all_items)} 条7天内的采购意向，开始抓取详情...")

        # 依次抓取每条记录的详情
        results = []
        for idx, item in enumerate(all_items, 1):
            print(f"({idx}/{len(all_items)}) 正在抓取: {item['title']}")
            detail = fetch_detail_content(item["url"])
            if detail:
                combined = {
                    "title": detail["title"] or item["title"],
                    "url": item["url"],
                    "date": item["date"],
                    "publish_date": detail["publish_date"],
                    "content": detail["content"]
                }
                results.append(combined)
            else:
                # 如果详情抓取失败，只保留列表信息
                results.append({
                    "title": item["title"],
                    "url": item["url"],
                    "date": item["date"],
                    "publish_date": "",
                    "content": "抓取失败"
                })
            # 适当延时，避免请求过快
            time.sleep(0.5)

        # 保存为 JSON 文件
        os.makedirs(DATA_DIR, exist_ok=True)
        output_file = os.path.join(DATA_DIR, "procurement_intentions_7days.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"爬取完成！共 {len(results)} 条数据，已保存至 {output_file}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
