from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os
import shutil
import time
from datetime import datetime, timedelta
import json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _make_driver():
    """创建 Chrome 浏览器驱动，通过环境变量 HEADLESS 控制是否无界面（默认无界面）"""
    options = Options()
    if os.environ.get("HEADLESS", "1") != "0":
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
    driver.maximize_window()
    return driver


def extract_recent_data(driver, pages=2, days=7, reference_date=None):
    """
    从当前搜索结果页面提取多页数据，并按日期筛选最近 days 天的记录。
    :param driver: 已处于搜索结果页的 WebDriver 实例
    :param pages: 要翻页的总页数（包括当前页）
    :param days: 筛选的天数范围（最近 days 天，含今天）
    :param reference_date: 参考日期，默认为当天（用于测试时可指定）
    :return: 符合条件的记录列表，每条记录包含 title, url, date（原始字符串）
    """
    if reference_date is None:
        reference_date = datetime.now().date()
    else:
        if isinstance(reference_date, str):
            reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()

    all_items = []
    wait = WebDriverWait(driver, 10)

    for page in range(1, pages + 1):
        wait.until(EC.presence_of_element_located((By.ID, "searchid")))
        items = driver.find_elements(By.CSS_SELECTOR, "#searchid > li")

        for item in items:
            try:
                link = item.find_element(By.TAG_NAME, "a")
                url = link.get_attribute("href")
                title = link.get_attribute("title") or link.text.strip()
                date_span = item.find_element(By.CLASS_NAME, "L_date")
                date_text = date_span.text.strip()
                clean_date = date_text.strip('[]').strip()
                item_date = datetime.strptime(clean_date, "%Y-%m-%d").date()

                all_items.append({
                    "title": title,
                    "url": url,
                    "date": item_date,
                    "date_str": date_text
                })
            except Exception as e:
                print(f"解析项出错: {e}")
                continue

        if page < pages:
            try:
                next_btn = driver.find_element(By.ID, "next")
                if "gray" in next_btn.get_attribute("class"):
                    print("下一页按钮不可用，停止翻页")
                    break
                next_btn.click()
                time.sleep(2)
            except Exception as e:
                print(f"翻页失败: {e}")
                break

    # 日期筛选
    cutoff_date = reference_date - timedelta(days=days)
    recent_items = [item for item in all_items if item["date"] >= cutoff_date]

    # 将日期还原为原始字符串
    for item in recent_items:
        item["date"] = item["date_str"]
        del item["date_str"]

    return recent_items


def extract_bulletin_content(driver, url):
    """
    访问公告详情页，点击"招标公告"选项卡，提取正文内容。
    :param driver: WebDriver实例
    :param url: 详情页URL
    :return: 正文文本内容，若提取失败返回空字符串
    """
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.presence_of_element_located((By.ID, "menu")))
        bulletin_tab = driver.find_element(By.LINK_TEXT, "招标公告")
        bulletin_tab.click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#tab1 .Article")))
        article = driver.find_element(By.CSS_SELECTOR, "#tab1 .Article")
        return article.text
    except Exception as e:
        print(f"提取正文失败: {url}, 错误: {e}")
        return ""


def run() -> tuple:
    """
    采集苏州市政府采购平台最近7天的招标公告。
    返回：(记录列表, 中间文件路径)，每条记录包含 title / url / date / content。
    中间文件带时间戳，供 pipeline 集成后删除。
    """
    driver = _make_driver()

    try:
        url = "https://czju.suzhou.gov.cn/zfcg/html/main/index.shtml"
        driver.get(url)
        print("[gov] 页面已打开")

        wait = WebDriverWait(driver, 10)
        region_select = wait.until(EC.presence_of_element_located((By.ID, "choose")))

        select = Select(region_select)
        select.select_by_value("苏州")
        print("[gov] 已选择区域：苏州市级")

        search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.button[value='搜 索']")))
        search_button.click()
        print("[gov] 已点击搜索按钮，等待跳转...")
        time.sleep(2)

        recent_data = extract_recent_data(driver, pages=3, days=7)
        print(f"共找到 {len(recent_data)} 条最近7天的记录")

        total = len(recent_data)
        success_count = 0
        for idx, item in enumerate(recent_data, 1):
            print(f"({idx}/{total}) 正在抓取: {item['title']}")
            content = extract_bulletin_content(driver, item["url"])
            item["content"] = content
            if content:
                success_count += 1

        print(f"共获取 {total} 条，{success_count} 条正文部分提取成功")

        # 生成带时间戳的中间文件
        os.makedirs(DATA_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        intermediate_file = os.path.join(DATA_DIR, f"intermediate_gov_{ts}.json")
        with open(intermediate_file, "w", encoding="utf-8") as f:
            json.dump(recent_data, f, ensure_ascii=False, indent=2)
        print(f"[gov] 中间文件已保存: {intermediate_file}")

        return recent_data, intermediate_file

    finally:
        driver.quit()


if __name__ == "__main__":
    result, intermediate_file = run()
    print(f"数据已保存至 {intermediate_file}")
