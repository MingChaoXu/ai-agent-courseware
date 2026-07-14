from selenium import webdriver
from selenium.common import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from PIL import Image
import base64
import requests
import io
import time
import json
import os
import shutil
from datetime import datetime, timedelta

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


# --- 1. 验证码识别函数 (基于硅基流动 SiliconFlow) ---
def call_siliconflow_vl(
        image_bytes,
        prompt="请识别这张图片中的验证码数字字母，只输出验证码内容，不要其他解释。",
        model="Qwen/Qwen3-VL-32B-Instruct",
        api_key=os.environ.get("SILICONFLOW_VL_API_KEY", ""),  # 从环境变量读取
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
        # 清理结果，去除可能存在的特殊字符或空格
        return ''.join(c for c in captcha_text if c.isalnum())
    except requests.exceptions.RequestException as e:
        print(f"验证码识别请求失败: {e}")
        if 'response' in locals():
            print(f"响应内容: {response.text}")
        return None  # 失败时返回None


# --- 2. 修复后的数据提取函数 ---
def extract_data_from_page(driver, page_num):
    """
    修复版：正确提取表格数据
    """
    wait = WebDriverWait(driver, 15)
    items = []

    try:
        print(f"正在等待第 {page_num} 页数据加载...")

        # 等待表格主体出现（增加超时时间）
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.conn_list_items")))

        # 稍微等待一下确保数据完全加载
        time.sleep(1)

        # 获取所有数据行（直接使用CSS选择器更可靠）
        row_elements = driver.find_elements(By.CSS_SELECTOR, "tbody.conn_list_items tr[href]")

        print(f"第 {page_num} 页检测到 {len(row_elements)} 条数据。")

        for index, row in enumerate(row_elements, 1):
            try:
                # --- 1. 提取链接 (从 tr 标签的 href 属性) ---
                relative_url = row.get_attribute("href")

                if not relative_url:
                    print(f"  第 {index} 行警告: 未找到 href 属性，跳过。")
                    continue

                # 拼接完整 URL
                if relative_url.startswith("/"):
                    full_url = f"http://www.ccgp-jiangsu.gov.cn{relative_url}"
                else:
                    full_url = relative_url

                # --- 2. 提取标题 ---
                # 方法1：从 a 标签获取（如果a标签有内容）
                try:
                    title_elem = row.find_element(By.CSS_SELECTOR, "td.col-title a")
                    title = title_elem.text.strip()
                except:
                    # 方法2：如果a标签没有文本，直接从td获取
                    title_elem = row.find_element(By.CSS_SELECTOR, "td.col-title")
                    title = title_elem.text.strip()

                if not title:
                    print(f"  第 {index} 行警告: 标题为空。")
                    continue

                # --- 3. 提取日期 ---
                date_elem = row.find_element(By.CSS_SELECTOR, "td.col-date")
                date = date_elem.text.strip()

                # --- 4. 提取地区（可选）---
                try:
                    area_elem = row.find_element(By.CSS_SELECTOR, "td.col-area")
                    area = area_elem.text.strip()
                except:
                    area = ""

                items.append({
                    "title": title,
                    "url": full_url,
                    "date": date,
                    "area": area,
                    "page": page_num
                })

                print(f"  ✓ 成功提取: {title[:30]}... ({date})")

            except NoSuchElementException as e:
                print(f"  解析第 {index} 行时缺失元素: {e}")
                continue
            except Exception as e:
                print(f"  解析第 {index} 行时发生未知错误: {e}")
                continue

        print(f"第 {page_num} 页成功提取 {len(items)} 条有效数据。")

        # 如果没有找到数据，尝试备用选择器
        if len(items) == 0:
            print("  尝试备用选择器...")
            row_elements = driver.find_elements(By.CSS_SELECTOR, "tbody.conn_list_items tr")
            print(f"  通过备用选择器找到 {len(row_elements)} 个tr元素")

            for index, row in enumerate(row_elements, 1):
                try:
                    # 检查是否有href属性
                    href = row.get_attribute("href")
                    if href:
                        print(f"  找到带href的行，尝试提取...")
                        # 重复上面的提取逻辑
                        full_url = f"http://www.ccgp-jiangsu.gov.cn{href}" if href.startswith("/") else href

                        title_elem = row.find_element(By.CSS_SELECTOR, "td.col-title")
                        title = title_elem.text.strip()

                        date_elem = row.find_element(By.CSS_SELECTOR, "td.col-date")
                        date = date_elem.text.strip()

                        items.append({
                            "title": title,
                            "url": full_url,
                            "date": date,
                            "area": "",
                            "page": page_num
                        })
                        print(f"  ✓ 备用方式提取: {title[:30]}...")
                except Exception as e:
                    continue

    except TimeoutException:
        print(f"第 {page_num} 页数据容器加载超时。")
        # 打印当前页面源码的前1000个字符用于调试
        print("当前页面源码片段:")
        print(driver.page_source[:1000])
    except Exception as e:
        print(f"提取第 {page_num} 页数据时发生严重错误: {e}")

    return items


# --- 2.1 日期过滤函数 ---
def filter_recent_week(data, days=7):
    """
    过滤出最近 days 天的数据。
    假设日期格式为 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM:SS'。
    """
    filtered = []
    today = datetime.now().date()
    start_date = today - timedelta(days=days)  # 包括今天和 days 天前
    for item in data:
        date_str = item.get('date', '').strip()
        if not date_str:
            continue
        # 尝试解析日期部分（可能包含时间）
        try:
            # 去除时间部分，取前10个字符（YYYY-MM-DD）
            date_part = date_str[:10]
            item_date = datetime.strptime(date_part, '%Y-%m-%d').date()
            if start_date <= item_date <= today:
                filtered.append(item)
        except ValueError:
            # 如果格式不匹配，跳过该项
            print(f"  警告: 无法解析日期 '{date_str}'，跳过")
            continue
    print(f"  日期过滤: 共 {len(data)} 条数据，保留最近 {days} 天数据 {len(filtered)} 条")
    return filtered


# --- 2.2 详情页内容提取函数（采购意向：直接爬取页面文字）---
def extract_detail_from_url(driver, url):
    """
    访问采购意向详情页，直接提取页面文字内容。
    采购意向页面结构：内容默认在 span#content1 中显示，
    无需点击任何公告进度tab，直接抓取文本即可。
    """
    try:
        print(f"正在访问详情页: {url}")
        driver.get(url)
        wait = WebDriverWait(driver, 30)
        # 等待页面基本加载
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        # 等待JS渲染内容
        time.sleep(3)

        # 提取标题
        title_text = ""
        try:
            title_elem = driver.find_element(By.CSS_SELECTOR, "span#newstitle1")
            title_text = title_elem.text.strip()
        except NoSuchElementException:
            pass

        # 提取发布时间
        date_text = ""
        try:
            date_elem = driver.find_element(By.CSS_SELECTOR, "span#newstime1")
            date_text = date_elem.text.strip()
        except NoSuchElementException:
            pass

        # 直接提取采购意向正文内容（span#content1 默认 display:block）
        content_text = ""
        try:
            content_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span#content1")))
            content_text = content_elem.text
        except TimeoutException:
            # 备选1：div.article_content
            try:
                content_elem = driver.find_element(By.CSS_SELECTOR, "div.article_content")
                content_text = content_elem.text
            except NoSuchElementException:
                # 备选2：div.article_p
                try:
                    content_elem = driver.find_element(By.CSS_SELECTOR, "div.article_p")
                    content_text = content_elem.text
                except NoSuchElementException:
                    # 备选3：整个页面正文
                    print(f"  无法找到内容元素，使用页面正文备用")
                    content_elem = driver.find_element(By.TAG_NAME, "body")
                    content_text = content_elem.text

        # 组装完整内容：标题 + 时间 + 正文
        parts = []
        if title_text:
            parts.append(title_text)
        if date_text:
            parts.append(f"发布时间：{date_text}")
        if content_text:
            parts.append(content_text)
        full_text = "\n".join(parts)

        # 清理多余的空白字符，保留换行
        lines = [line.strip() for line in full_text.split('\n')]
        lines = [line for line in lines if line]  # 移除空行
        cleaned_content = '\n'.join(lines)
        return cleaned_content
    except TimeoutException:
        print(f"  超时: 无法加载详情页 {url}")
        return ""
    except Exception as e:
        print(f"  提取详情页内容时出错: {e}")
        return ""


# --- 3. 主程序 (Selenium 爬虫) ---
def run() -> tuple:
    """
    采集江苏省政府采购平台「采购意向」。
    返回：(结果列表, 中间文件路径)。中间文件带时间戳，供 pipeline 集成后删除。
    """
    # 初始化浏览器 (Edge)
    # 如果你使用 Chrome，请替换为 webdriver.Chrome() 并配置 Service
    driver = _make_driver()
    wait = WebDriverWait(driver, 15)  # 增加等待时间以防网络慢

    all_data = []  # 用于存储所有页面的数据

    try:
        # 3.1 打开网页（采购意向）
        driver.get("http://www.ccgp-jiangsu.gov.cn/jiangsu/cggg_search.html?lmid=cgyx&qh=notic_c1")

        # --- 3.2 表单选择逻辑 ---

        # 时间：近一个月 (data='30')
        month_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='date']/li/a[@data='30']")))
        month_link.click()
        time.sleep(1)  # 点击后稍作等待

        # 地区选择：苏州市 (下拉框)
        zone_select = Select(driver.find_element(By.ID, "zone"))
        zone_select.select_by_value("320500")
        time.sleep(2)  # 等待异步加载

        # 地区选择：市本级 (点击链接)
        city_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='zone_c']/li/a[@data='320500']")))
        city_link.click()
        time.sleep(1)

        # 公告类型：采购意向
        notice_type_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='cgtype']/li/a[@data='cgyx']")))
        notice_type_link.click()
        time.sleep(1)

        # --- 3.3 验证码处理与识别（带重试机制）---
        max_retries = 3
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            print(f"正在处理验证码（第 {retry_count + 1} 次尝试）...")
            try:
                # 获取验证码图片元素
                captcha_img = driver.find_element(By.ID, "validateCodeImg")
                # 截取验证码图片为字节流
                captcha_png_bytes = captcha_img.screenshot_as_png

                # 调用 AI 识别
                captcha_text = call_siliconflow_vl(captcha_png_bytes)

                if not captcha_text or len(captcha_text) < 4:
                    print("验证码识别失败或结果太短，将刷新验证码重试。")
                    # 点击验证码图片刷新
                    captcha_img.click()
                    time.sleep(1)
                    retry_count += 1
                    continue

                print(f"AI识别结果: {captcha_text}")

                # 填充验证码
                input_field = driver.find_element(By.ID, "validateCode")
                input_field.clear()
                input_field.send_keys(captcha_text)

                # --- 3.4 点击搜索 ---
                search_button = driver.find_element(By.XPATH, "//button[@class='q_submit']")
                search_button.click()
                print("已点击搜索，等待结果页面加载...")
                # 增加等待时间，让页面完全加载
                time.sleep(5)

                # --- 检查是否成功 ---
                # 首先检查是否有错误消息（验证码错误）
                errmsg_elements = driver.find_elements(By.ID, "errmsg")
                if errmsg_elements:
                    error_text = errmsg_elements[0].text.strip()
                    # 检查错误消息是否包含验证码错误关键词
                    if error_text and ('验证码' in error_text or '不正确' in error_text):
                        print(f"验证码错误: {error_text}")
                        # 刷新验证码图片
                        captcha_img.click()
                        time.sleep(1)
                        retry_count += 1
                        continue
                
                # 检查是否成功加载结果页面（检测表格内容）
                # 多等待几秒让表格内容加载
                time.sleep(3)
                
                # 检测表格内容是否出现（检查 tbody.conn_list_items 是否有行数据）
                try:
                    # 等待表格数据行出现
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.conn_list_items tr[href]"))
                    )
                    # 检查是否有实际数据行
                    data_rows = driver.find_elements(By.CSS_SELECTOR, "tbody.conn_list_items tr[href]")
                    if len(data_rows) > 0:
                        print(f"成功加载表格，检测到 {len(data_rows)} 条数据。")
                        success = True
                        break
                    else:
                        print("表格已加载但未检测到数据行，可能为空或验证码错误。")
                        # 刷新验证码图片重试
                        captcha_img.click()
                        time.sleep(1)
                        retry_count += 1
                        continue
                except TimeoutException:
                    # 如果找不到数据行，尝试其他选择器
                    try:
                        # 检查是否有表格容器
                        table = driver.find_element(By.CSS_SELECTOR, "table.no_tableBox")
                        # 检查表格是否可见（display 不为 none）
                        if table.is_displayed():
                            print("表格已显示，但未找到数据行。")
                            # 可能表格为空，检查是否有"empty_data"提示
                            empty_elements = driver.find_elements(By.CSS_SELECTOR, "div.empty_data")
                            if empty_elements and empty_elements[0].is_displayed():
                                print("表格为空，可能是查询条件无结果。")
                                # 这种情况不算验证码错误，跳出循环继续执行
                                success = True
                                break
                            else:
                                print("表格显示但无数据，可能验证码错误。")
                                captcha_img.click()
                                time.sleep(1)
                                retry_count += 1
                                continue
                        else:
                            print("表格存在但被隐藏，可能验证码错误。")
                            captcha_img.click()
                            time.sleep(1)
                            retry_count += 1
                            continue
                    except NoSuchElementException:
                        print("未检测到表格，可能验证码错误或页面加载失败。")
                        # 刷新验证码图片重试
                        captcha_img.click()
                        time.sleep(1)
                        retry_count += 1
                        continue

            except Exception as e:
                print(f"验证码处理过程中发生异常: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    print("将重试...")
                    time.sleep(2)
                continue

        if not success:
            print("验证码重试次数已达上限，脚本退出。")
            input("按回车键关闭浏览器...")
            return [], ""

        # --- 3.5 数据爬取 (第一页和第二页) ---
        all_data = []

        # --- 爬取第一页 ---
        page_1_data = extract_data_from_page(driver, 1)
        all_data.extend(page_1_data)

        # --- 爬取第二页 ---
        if len(page_1_data) > 0:  # 只有第一页有数据才翻页
            try:
                # 等待下一页按钮可点击
                next_page_btn = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//li[@class='js-page-next js-page-action ui-pager']"))
                )
                next_page_btn.click()
                print("已点击下一页...")

                # 等待分页控件状态改变或新数据加载（防止点击过快）
                time.sleep(2)

                # 检查是否真的翻页了（例如当前页码是否变为2）
                current_page = wait.until(
                    EC.presence_of_element_located((By.XPATH, "//li[@class='ui-pager focus' and text()='2']"))
                )
                print("确认已进入第二页。")

                page_2_data = extract_data_from_page(driver, 2)
                all_data.extend(page_2_data)

            except TimeoutException:
                print("翻页失败或只有一页数据。")
            except Exception as e:
                print(f"翻页过程异常: {e}")

        # --- 3.5 数据过滤（最近一周）---
        filtered_data = filter_recent_week(all_data, days=7)
        all_data = filtered_data
        print(f"共找到 {len(all_data)} 条最近7天的记录")

        # --- 3.6 提取详情页内容 ---
        total = len(all_data)
        success_count = 0
        if all_data:
            for i, item in enumerate(all_data, 1):
                print(f"({i}/{total}) 正在抓取: {item['title']}")
                content = extract_detail_from_url(driver, item['url'])
                item['content'] = content
                if content:
                    success_count += 1
                # 避免请求过快，稍作延迟
                time.sleep(1)
        else:
            print("没有数据可提取详情页内容。")

        print(f"共获取 {total} 条，{success_count} 条正文部分提取成功")

        # --- 3.6 保存为带时间戳的中间文件（供 pipeline 集成后删除）---
        intermediate_file = ""
        if all_data:
            os.makedirs(DATA_DIR, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            intermediate_file = os.path.join(DATA_DIR, f"intermediate_js2_{ts}.json")
            with open(intermediate_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=4)
            print(f"\n成功！共爬取 {len(all_data)} 条数据，已保存至 '{intermediate_file}'")
        else:
            print("警告：未提取到任何数据。")


    except Exception as e:
        print(f"发生错误: {e}")


    finally:
        driver.quit()



    return all_data, intermediate_file
def main():
    data, intermediate_file = run()
    if data:
        print(f"\n成功！共爬取 {len(data)} 条数据，已保存至 '{intermediate_file}'")
    else:
        print("警告：未提取到任何数据。")

if __name__ == "__main__":
    main()
