import time
import json
import re
import os
import shutil
from datetime import datetime, timedelta
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def select_area_by_js(driver, select_id, value):
    """
    通过 JavaScript 设置 Chosen 下拉框的值
    :param driver: Selenium WebDriver
    :param select_id: 原始 select 元素的 ID
    :param value: 要选中的选项值
    """
    select = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, select_id))
    )
    js_code = f"""
        var $select = $('#{select_id}');
        if ($select.length) {{
            $select.val('{value}').trigger('chosen:updated');
            return true;
        }} else {{
            return false;
        }}
    """
    result = driver.execute_script(js_code)
    if not result:
        raise Exception(f"未找到 ID 为 {select_id} 的元素，或 jQuery 未加载")


def scrape_detail_page(driver, item, base_url):
    """
    访问详情页，提取标题、发布日期和正文内容
    """
    url = item['link']
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.con'))
    )
    try:
        title_elem = driver.find_element(By.CSS_SELECTOR, 'div.article-info h1')
        title = title_elem.text.strip()
    except:
        title = item['title']

    date_str = ""
    try:
        info_source = driver.find_element(By.CSS_SELECTOR, 'p.info-sources')
        text = info_source.text
        match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if match:
            date_str = match.group(1)
        date_str = f"[{date_str} ]"
    except:
        date_str = item['publish_time']

    try:
        content_elem = driver.find_element(By.CSS_SELECTOR, 'div.con')
        content = content_elem.text.strip()
    except:
        content = ""

    return {
        'title': title,
        'url': url,
        'date': date_str,
        'content': content
    }


def setup_driver():
    """配置并返回 Chrome 浏览器驱动，通过环境变量 HEADLESS 控制是否无界面（默认无界面）"""
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


def scrape_current_page(driver, base_url):
    page_data = []
    row_count = len(driver.find_elements(By.CSS_SELECTOR, 'tbody#xxList tr'))
    for index in range(row_count):
        for attempt in range(3):
            try:
                row = driver.find_elements(By.CSS_SELECTOR, 'tbody#xxList tr')[index]
                title_elem = row.find_element(By.CSS_SELECTOR, 'td:nth-child(2) a')
                title = title_elem.get_attribute('title') or title_elem.text.strip()
                href = title_elem.get_attribute('href')
                full_link = urljoin(base_url, href) if href else None
                time_elem = row.find_element(By.CSS_SELECTOR, 'td:nth-child(4)')
                pub_time = time_elem.text.strip()
                page_data.append({
                    'title': title,
                    'link': full_link,
                    'publish_time': pub_time
                })
                break
            except (StaleElementReferenceException, IndexError) as e:
                if attempt == 2:
                    print(f"第 {index + 1} 行数据提取失败（重试{attempt + 1}次）: {e}")
                else:
                    time.sleep(0.5)
            except NoSuchElementException as e:
                print(f"第 {index + 1} 行缺少必要元素: {e}")
                break
            except Exception as e:
                print(f"第 {index + 1} 行未知错误: {e}")
                break
    return page_data


def get_total_pages(driver):
    """尝试从分页控件中获取总页数，返回整数，如果无法获取则返回None"""
    try:
        page_lis = driver.find_elements(By.CSS_SELECTOR, '#pager ul.m-pagination-page li')
        if page_lis:
            last_li = page_lis[-1]
            last_page_index = int(last_li.find_element(By.TAG_NAME, 'a').get_attribute('data-page-index'))
            return last_page_index + 1
    except:
        pass
    try:
        total_text = driver.find_element(By.CSS_SELECTOR, '#pager .m-pagination-info').text
        match = re.search(r'共(\d+)页', total_text)
        if match:
            return int(match.group(1))
    except:
        pass
    return None


def get_current_page_index(driver):
    """获取当前页码的索引（0-based），若未找到则返回0"""
    try:
        active_li = driver.find_element(By.CSS_SELECTOR, '#pager ul.m-pagination-page li.active')
        return int(active_li.find_element(By.TAG_NAME, 'a').get_attribute('data-page-index'))
    except:
        return 0


def go_to_page(driver, page_index):
    """
    跳转到指定页码（page_index为0-based索引）
    优先点击页码链接，失败时使用跳转输入框；全程使用JavaScript操作以避免stale element
    返回 True 表示跳转成功，False 表示跳转失败
    """
    try:
        # 方式1：直接点击页码链接（使用JS避免stale element）
        script_click = f"""
        var link = document.querySelector('#pager ul.m-pagination-page li a[data-page-index="{page_index}"]');
        if (link) {{
            link.click();
            return true;
        }}
        return false;
        """
        if driver.execute_script(script_click):
            # 检查是否出现Alert（页码超出范围时可能弹出）
            try:
                WebDriverWait(driver, 1).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                alert_text = alert.text
                print(f"跳转时出现Alert: {alert_text}")
                alert.accept()
                return False
            except TimeoutException:
                pass
            return True

        # 方式2：使用跳转输入框（使用JS避免stale element）
        script_jump = f"""
        var input = document.querySelector('#pager .m-pagination-jump input[data-page-btn="jump"]');
        var button = document.querySelector('#pager .m-pagination-jump button[data-page-btn="jump"]');
        if (input && button) {{
            input.value = '{page_index + 1}';
            var event = new Event('input', {{ bubbles: true }});
            input.dispatchEvent(event);
            button.click();
            return true;
        }}
        return false;
        """
        if driver.execute_script(script_jump):
            try:
                WebDriverWait(driver, 2).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                alert_text = alert.text
                print(f"跳转时出现Alert: {alert_text}")
                alert.accept()
                return False
            except TimeoutException:
                pass
            return True

        print(f"未找到页码 {page_index + 1} 的跳转元素")
        return False
    except Exception as e:
        print(f"执行跳转操作时出错：{e}")
        return False


def wait_for_page_change(driver, old_first_title=None, timeout=10):
    """
    等待页面翻页后的加载完成。
    通过检测表格第一行内容是否变化（或等待旧行消失）来判断。
    """
    if old_first_title is None:
        try:
            old_first_title = driver.find_element(By.CSS_SELECTOR, 'tbody#xxList tr:first-child td:nth-child(2) a').text
        except:
            old_first_title = None
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, 'tbody#xxList tr')) > 0 and
                      (old_first_title is None or
                       d.find_element(By.CSS_SELECTOR, 'tbody#xxList tr:first-child td:nth-child(2) a').text != old_first_title)
        )
        return True
    except TimeoutException:
        return False


def filter_last_7_days(data):
    """
    从数据中筛选出最近7天（含今天）的记录，并返回筛选后的列表。
    同时检查每一天是否有数据，缺失则输出提示。
    """
    today = datetime.now().date()
    start_date = today - timedelta(days=7)
    date_set = set()
    filtered = []
    for item in data:
        try:
            pub_date = datetime.strptime(item['publish_time'], '%Y-%m-%d').date()
            if start_date <= pub_date <= today:
                filtered.append(item)
                date_set.add(pub_date)
        except ValueError:
            continue
    current = start_date
    missing_dates = []
    while current <= today:
        if current not in date_set:
            missing_dates.append(current)
        current += timedelta(days=1)
    if missing_dates:
        print("以下日期无数据：")
        for d in missing_dates:
            print(d.strftime('%Y-%m-%d'))
    else:
        print("最近7天每天都有数据。")
    return filtered


def main():
    url = "http://szzyjy.com.cn:8086/jyxx/tradeInfo.html"
    base_url = "http://szzyjy.com.cn:8086"
    driver = setup_driver()
    wait = WebDriverWait(driver, 10)
    all_data = []

    try:
        # 1. 打开网页
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ewb-trade-mid")))

        # 选择交易信息类别为"国企采购及其他交易"
        trade_cat_li = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'li.catetype[data-type="003034"]')))
        if 'active' not in trade_cat_li.get_attribute('class'):
            trade_cat_li.click()
            print("已点击'国企采购及其他交易'")
            time.sleep(0.5)
        else:
            print("'国企采购及其他交易'已经是选中状态")

        info_type_li = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'li.jytype[data-catenum="003034001"]')))
        if 'active' not in info_type_li.get_attribute('class'):
            info_type_li.click()
            print("已点击'招标公告'")
            time.sleep(0.5)
        else:
            print("'招标公告'已经是选中状态")

        # 2. 选择发布时间为"近一月"
        time_li = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'li.timetype[data-timetype="30"]')))
        if 'active' not in time_li.get_attribute('class'):
            time_li.click()
            print("已点击'近一月'")
        else:
            print("'近一月'已经是选中状态")
        time.sleep(0.5)

        # 3. 设置所属区域
        select_area_by_js(driver, "xiaqutxt2", "苏州市")
        time.sleep(0.5)
        select_area_by_js(driver, "suzhou2", "苏州市区")
        print("已通过 JS 设置区域：苏州市 / 苏州市区")
        time.sleep(0.5)

        # 4. 点击搜索按钮
        search_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.ewb-sbtn')))
        search_btn.click()
        print("已点击搜索按钮")

        # 5. 等待搜索结果加载
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody#xxList tr")))
        print("搜索结果已加载")

        # 6. 获取当前页码索引（0-based）
        current_page_index = get_current_page_index(driver)

        # 7. 确定要抓取的页数：最多3页，但如果总页数小于3则抓取全部
        total_pages = get_total_pages(driver)
        max_pages_to_fetch = 3
        if total_pages is not None:
            max_pages_to_fetch = min(3, total_pages)
            print(f"总页数：{total_pages}，将抓取前 {max_pages_to_fetch} 页")
        else:
            print("无法获取总页数，将尝试抓取前3页，翻页失败时停止")

        page_count = 0
        while page_count < max_pages_to_fetch:
            print(f"正在抓取第 {current_page_index + 1} 页...")
            page_data = scrape_current_page(driver, base_url)
            all_data.extend(page_data)
            print(f"第 {current_page_index + 1} 页抓取到 {len(page_data)} 条记录")
            page_count += 1

            if page_count >= max_pages_to_fetch:
                print(f"已达到最大抓取页数{max_pages_to_fetch}页，停止翻页")
                break

            # 尝试跳转到下一页
            next_page_index = current_page_index + 1
            try:
                old_title = driver.find_element(By.CSS_SELECTOR, 'tbody#xxList tr:first-child td:nth-child(2) a').text
            except:
                old_title = None

            if go_to_page(driver, next_page_index):
                if wait_for_page_change(driver, old_title):
                    print(f"成功跳转到第 {next_page_index + 1} 页")
                    current_page_index = next_page_index
                else:
                    print("等待新页加载超时，可能已无更多数据或页面无数据，停止翻页")
                    break
            else:
                print("无法跳转到下一页（可能已到达最后一页），停止翻页")
                break

        time.sleep(0.5)

        # 8. 筛选最近7天的数据
        print("\n开始筛选最近7天的数据...")
        filtered_data = filter_last_7_days(all_data)
        print(f"共找到 {len(filtered_data)} 条最近7天的记录")

        # 9. 遍历每个详情链接，获取页面内容
        total = len(filtered_data)
        success_count = 0
        details = []
        for idx, item in enumerate(filtered_data, 1):
            print(f"({idx}/{total}) 正在抓取: {item['title']}")
            try:
                detail = scrape_detail_page(driver, item, base_url)
                if detail and detail.get("content"):
                    details.append(detail)
                    success_count += 1
                else:
                    # 提取失败也保留数据，content 为空
                    details.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "date": item.get("publish_time", ""),
                        "content": ""
                    })
                time.sleep(0.5)
            except Exception as e:
                print(f"处理详情页时出错: {e}")
                # 异常情况也保留数据，content 为空
                details.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "date": item.get("publish_time", ""),
                    "content": ""
                })
                continue

        print(f"共获取 {total} 条，{success_count} 条正文部分提取成功")

        # 10. 保存详情数据为带时间戳的中间文件（供 pipeline 集成后删除）
        os.makedirs(DATA_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        detail_output_file = os.path.join(DATA_DIR, f"intermediate_public_{ts}.json")
        with open(detail_output_file, 'w', encoding='utf-8') as f:
            json.dump(details, f, ensure_ascii=False, indent=2)
        print(f"详情页数据已保存至 {detail_output_file}")

        return details, detail_output_file

    except Exception as e:
        print(f"发生错误：{e}")
        return [], ""
    finally:
        driver.quit()


# 供外部整合调用的入口别名
def run() -> tuple:
    """采集苏州招投标网最近7天国企采购招标公告，返回 (结果列表, 中间文件路径)。"""
    return main()


if __name__ == "__main__":
    results, intermediate_file = main()
    print(f"数据已保存至 {intermediate_file}")
