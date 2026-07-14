import time
import re
import base64
import os
import shutil
import requests
import json
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _make_driver():
    """创建 Chrome 浏览器驱动，通过环境变量 HEADLESS 控制是否无界面（默认无界面）"""
    options = Options()
    if os.environ.get("HEADLESS", "1") != "0":
        # 用新版 headless（Chrome 109+），渲染行为更接近真实浏览器
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # 不再禁用 GPU，避免 canvas/验证码渲染异常
        # 显式设置窗口尺寸，确保元素在视口内（headless 下 maximize_window 不可靠）
        options.add_argument("--window-size=1920,1080")
    else:
        options.add_argument("--no-sandbox")
    # 显式指定 chromedriver 路径，避免 selenium-manager 联网检查
    chromedriver_path = (
        os.environ.get("CHROMEDRIVER_PATH")
        or shutil.which("chromedriver")
        or "/usr/local/bin/chromedriver"
    )
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(1920, 1080)
    return driver


# ---------- 硅基流动视觉模型识别验证码 ----------
def call_siliconflow_vl(
        image_bytes,
        prompt="请识别这张图片中的验证码数字字母，只输出验证码内容，不要其他解释。",
        model="Qwen/Qwen3-VL-32B-Instruct",
        api_key=os.environ.get("SILICONFLOW_VL_API_KEY", ""),
        mime_type="image/png",
        max_tokens=512
):
    """调用硅基流动的视觉语言模型识别验证码"""
    img_base64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{img_base64}"

    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url, "detail": "high"}
                    },
                    {"type": "text", "text": prompt}
                ]
            }
        ],
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        captcha_text = result["choices"][0]["message"]["content"]
        return captcha_text.strip()
    except requests.exceptions.RequestException as e:
        print(f"验证码识别请求失败: {e}")
        if 'response' in locals():
            print(f"响应内容: {response.text}")
        raise


# ---------- 解析当前页公告（仅当页面已存在至少一个块时调用） ----------
def parse_current_page(driver):
    """返回当前页的公告列表，每个元素为 (title, url, date)"""
    items = []
    index = 1
    while True:
        try:
            block = driver.find_element(By.XPATH,
                f"(//div[@id='noticeUl']//div[contains(@class, 'cfcpn-list-main')])[{index}]")
            title_elem = block.find_element(By.CSS_SELECTOR, "h5 a")
            title = title_elem.get_attribute("title") or title_elem.text
            onclick = title_elem.get_attribute("onclick")
            match = re.search(r"noticeDetail\('([^']+)'", onclick)
            if match:
                notice_id = match.group(1)
                # 修改为新的URL格式
                url = f"http://www.cfcpn.com/jcw/sys/index/goUrl?url=modules/sys/login/detail&column=undefined&searchVal={notice_id}"
            else:
                url = "javascript:void(0);"
            date_elem = block.find_element(By.CSS_SELECTOR, "h6.text-muted")
            date = date_elem.text.strip()
            items.append((title, url, date))
            index += 1
        except Exception:
            break
    return items


# ---------- 等待搜索结果出现（至少一个公告块） ----------
def wait_for_search_results(driver, timeout=20):
    """等待搜索结果加载完成，返回 True 表示有结果，False 表示无结果或超时"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "noticeUl"))
        )
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@id='noticeUl']//div[contains(@class, 'cfcpn-list-main')]")
            )
        )
        return True
    except Exception as e:
        print(f"等待搜索结果超时或没有公告块: {e}")
        return False


# ---------- 从详情页提取正文 ----------
def extract_detail_content(driver, url, timeout=15):
    """
    访问详情页，提取正文内容。
    处理可能出现的"您点的太快了"弹窗，并返回正文文本。
    """
    try:
        driver.get(url)
        # 处理可能出现的 alert 弹窗（如频率限制）
        try:
            # 等待 alert 出现（最多2秒）
            alert = WebDriverWait(driver, 2).until(EC.alert_is_present())
            alert.accept()
            print("已处理 alert 弹窗（您点的太快了）")
        except:
            pass  # 没有弹窗，继续执行

        # 等待正文区域加载
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "detail-new"))
        )
        content_elem = driver.find_element(By.ID, "detail-new")
        # 获取纯文本（去除HTML标签）
        text = content_elem.text
        # 清理多余的空白行
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    except Exception as e:
        print(f"提取正文失败 {url}: {e}")
        return None


# ---------- 解析日期字符串（支持多种格式） ----------
def parse_date(date_str):
    """
    将列表页的日期字符串转为 datetime.date 对象。
    支持格式: "[2026-03-19 ]"、"2026-03-19"、"2026-03-19 08:41:21" 等。
    """
    match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
    if match:
        return datetime.datetime.strptime(match.group(1), "%Y-%m-%d").date()
    else:
        raise ValueError(f"无法解析日期: {date_str}")


# ---------- 主流程 ----------
def main():
    driver = _make_driver()

    try:
        # 1. 登录
        login_url = "http://www.cfcpn.com/jcw/supplierLogin"

        max_retries = 10
        for attempt in range(1, max_retries + 1):
            try:
                driver.get(login_url)
                wait = WebDriverWait(driver, 10)

                # 定位输入框
                username_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
                password_input = driver.find_element(By.ID, "password")
                captcha_input = driver.find_element(By.ID, "validateCode")

                # 输入账号密码
                username_input.send_keys("SZDXJRJ")
                password_input.send_keys("Szdx1@")

                # 获取验证码图片并识别
                captcha_img = driver.find_element(By.CLASS_NAME, "validateImg")
                # 滚动到验证码元素可见，确保在视口内（headless 下必需）
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", captcha_img)
                time.sleep(1.5)  # 等待图片渲染完成
                captcha_png = captcha_img.screenshot_as_png
                captcha_text = call_siliconflow_vl(captcha_png)
                print(f"识别出的验证码: {captcha_text}")

                # 输入验证码并点击登录
                captcha_input.send_keys(captcha_text)
                login_button = wait.until(EC.element_to_be_clickable((By.ID, "sign")))
                login_button.click()

                # 等待登录成功的标志（首页右上角元素）
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cfcpn-topbar-right")))
                print("登录成功，进入首页")
                break  # 登录成功，退出循环

            except Exception as e:
                print(f"登录失败 (尝试 {attempt}/{max_retries}): {e}")
                if attempt == max_retries:
                    print("达到最大尝试次数，登录失败")
                    raise  # 或根据业务需求处理失败情况
                # 等待片刻后继续下一次尝试（循环将重新加载页面）
                time.sleep(2)

        # 2. 进入采购公告列表页
        list_url = "http://www.cfcpn.com/jcw/sys/index/goUrl?url=modules/sys/login/list&column=cggg"
        driver.get(list_url)

        wait.until(EC.presence_of_element_located((By.ID, "region")))

        # 3. 选择江苏省并搜索
        region_select = Select(driver.find_element(By.ID, "region"))
        region_select.select_by_visible_text("江苏省")
        print("已选择江苏省")
        driver.find_element(By.ID, "searchBtn").click()
        print("已点击搜索按钮，等待结果加载...")

        if not wait_for_search_results(driver, timeout=30):
            print("搜索超时或没有返回任何公告，请检查网络或网站状态。")
            return [], ""

        print("第一页搜索结果已加载")

        # 4. 爬取前6页数据
        all_data = []
        max_pages = 8
        current_page = 1
        time.sleep(5)
        while current_page <= max_pages:
            print(f"正在爬取第 {current_page} 页...")

            page_data = parse_current_page(driver)
            all_data.extend(page_data)
            print(f"第 {current_page} 页共获取 {len(page_data)} 条公告")

            if current_page >= max_pages:
                break

            # 翻页
            try:
                old_first_title = driver.find_element(By.XPATH,
                    "//div[@id='noticeUl']//div[contains(@class, 'cfcpn-list-main')][1]//h5/a").text
            except:
                old_first_title = None

            next_btn = driver.find_element(By.ID, "img_next")
            next_btn.click()
            print(f"点击下一页，等待第 {current_page + 1} 页加载...")

            if old_first_title:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (By.XPATH,
                         f"//div[@id='noticeUl']//div[contains(@class, 'cfcpn-list-main')][1]//h5/a[not(text()='{old_first_title}')]")
                    )
                )
            else:
                WebDriverWait(driver, 15).until(
                    EC.staleness_of(driver.find_element(By.ID, "noticeUl"))
                )
            time.sleep(10)
            current_page += 1

        print(f"\n共采集 {len(all_data)} 条公告")

        # 5. 筛选7天内且标题包含"苏州"的公告
        today = datetime.date.today()
        seven_days_ago = today - datetime.timedelta(days=7)
        filtered = []
        for title, url, date_str in all_data:
            try:
                pub_date = parse_date(date_str)
                # 修改点1：增加标题包含"苏州"的筛选
                if pub_date > seven_days_ago and "苏州" in title:
                    filtered.append((title, url, date_str, pub_date))
            except ValueError as e:
                print(f"日期解析失败: {date_str}，跳过该条")
                continue

        print(f"共找到 {len(filtered)} 条最近7天的记录")

        if not filtered:
            print("没有符合条件的公告，程序结束。")
            return [], ""

        # 6. 依次访问详情页，提取正文（每次访问后间隔15秒）
        total = len(filtered)
        success_count = 0
        results = []
        for idx, (title, url, date_str, pub_date) in enumerate(filtered, 1):
            print(f"({idx}/{total}) 正在抓取: {title}")
            content = extract_detail_content(driver, url)
            if content:
                results.append({
                    "title": title,
                    "url": url,
                    "date": date_str,
                    "content": content
                })
                success_count += 1
            else:
                # 提取失败也保留数据，content 为空
                results.append({
                    "title": title,
                    "url": url,
                    "date": date_str,
                    "content": ""
                })
            # 修改点2：间隔时间改为15秒
            time.sleep(30)

        print(f"共获取 {total} 条，{success_count} 条正文部分提取成功")

        # 7. 保存为带时间戳的中间文件（供 pipeline 集成后删除）
        os.makedirs(DATA_DIR, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(DATA_DIR, f"intermediate_jc_{ts}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n已保存 {len(results)} 条公告详情到 {output_file}")

        return results, output_file

    finally:
        driver.quit()


# 供外部整合调用的入口别名
def run() -> tuple:
    """采集全国采购网(cfcpn)中苏州相关最近7天招标公告，返回 (结果列表, 中间文件路径)。"""
    return main()


if __name__ == "__main__":
    results, intermediate_file = main()
    print(f"数据已保存至 {intermediate_file}")
