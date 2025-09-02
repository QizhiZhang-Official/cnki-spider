from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import time
import csv
import os

# =============================
# 配置参数
# =============================
SEARCH_KEYWORD = "低空经济"
MAX_PAGES_PER_THEME = 5
OUTPUT_DIR = "./cnki_low_air_economy"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =============================
# 初始化 Edge 浏览器
# =============================
def setup_driver():
    edge_options = EdgeOptions()
    edge_options.add_argument("--start-maximized")
    edge_options.add_argument("--disable-extensions")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")

    # 指定 EdgeDriver 路径 (请修改为你实际的路径)
    service = Service(executable_path=r'./msedgedriver.exe')

    driver = webdriver.Edge(service=service, options=edge_options)
    return driver

# =============================
# 等待元素可见
# =============================
def wait_until_visible(driver, by, selector):
    wait = WebDriverWait(driver, 10)
    return wait.until(
        EC.presence_of_element_located((by, selector))
    )


# =============================
# 获取所有主题选项
# =============================
def get_themes(driver):
    themes = []
    try:
        print("等待左侧筛选栏加载...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "divGroup"))
        )
        print("'divGroup' 容器已加载")

        # --- 关键修改点: 使用正确的属性定位 dd ---
        main_theme_dd = None
        try:
            print("尝试通过 field 和 tit 定位 '主要主题' 容器...")
            main_theme_dd = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "dd[field='ZYZT'][tit='主要主题']"))
            )
            print("成功通过 field 和 tit 定位")
        except TimeoutException:
            print("通过 field 和 tit 定位失败，尝试 fallback...")
            div_group = driver.find_element(By.ID, "divGroup")
            dl_elements = div_group.find_elements(By.TAG_NAME, "dl")
            if dl_elements:
                dd_elements = dl_elements[0].find_elements(By.TAG_NAME, "dd")
                for dd in dd_elements:
                    if "主要主题" in (dd.get_attribute("tit") or ""):
                        main_theme_dd = dd
                        print("通过 tit 属性在 dl/dd 结构中找到 '主要主题'")
                        break
                if not main_theme_dd and dd_elements:
                    print("未通过 tit 找到，使用第一个 dd 作为 fallback...")
                    main_theme_dd = dd_elements[0]

            if not main_theme_dd:
                raise NoSuchElementException("无法定位到 '主要主题' 的 dd 容器")

        print("开始查找主题选项...")
        # 等待 ul 出现
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "dd[field='ZYZT'] ul")) 
        )
        # 查找所有 li
        theme_li_elements = main_theme_dd.find_elements(By.TAG_NAME, "li")
        print(f"最终找到 {len(theme_li_elements)} 个主题项")
        
        for i, li in enumerate(theme_li_elements):
            try:
                # --- 关键修改点: 从 input 或 a 标签获取主题名 ---
                # 优先从 input 的 value 属性获取
                input_tag = li.find_element(By.TAG_NAME, "input")
                value = input_tag.get_attribute("value") or input_tag.get_attribute("text")
                if not value:
                    continue
                
                # --- 关键修改点: 从 span 标签获取数量 ---
                # 数量信息在 <span> 标签里，可能包含在 a 标签内
                span_tags = li.find_elements(By.TAG_NAME, "span")
                count_text = ""
                for span in span_tags:
                    span_text = span.text.strip()
                    if span_text and "(" in span_text and ")" in span_text:
                        count_text = span_text
                        break
                
                # 如果没有找到 span，再尝试从 a 标签的 text 中找
                if not count_text:
                    a_tags = li.find_elements(By.TAG_NAME, "a")
                    for a in a_tags:
                        a_text = a.text.strip()
                        if "(" in a_text and ")" in a_text:
                            count_text = a_text
                            break
                
                # 提取主题名和数量
                theme_name = ""
                count = 0
                if count_text and "(" in count_text:
                    parts = count_text.split("(")
                    theme_name = parts[0].strip()
                    count_str = parts[1].split(")")[0]
                    try:
                        count = int(count_str.rstrip('+'))
                    except ValueError:
                        print(f"  警告：第 {i+1} 项数量格式不标准: '{count_str}'")
                
                if theme_name and count > 0:
                    themes.append({"name": theme_name, "count": count})
                    print(f"  添加主题: {theme_name} ({count}篇)")
                else:
                    # 即使数量为0，也打印出来，方便调试
                    print(f"  (调试) 跳过项 - 名称: '{theme_name}', 数量文本: '{count_text}' (解析出数量: {count})")

            except Exception as e:
                print(f"  跳过第 {i+1} 个 li 元素，缺少必要子元素: {e.msg}")
                continue
                
    except Exception as e:
        print(f"获取主题失败: {e}")
        import traceback
        traceback.print_exc()
    
    return themes

# =============================
# 选择某个主题并爬取数据
# =============================
def crawl_by_theme(driver, theme_name):
    data = []
    try:
        # --- 关键修改点 1: 将主要逻辑封装在重试循环中 ---
        # 最多重试 3 次，以应对 StaleElementReferenceException
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"  (尝试 {attempt + 1}/{max_retries}) 查找主要主题区域...")
                # 重新定位 "主要主题" 区域 (关键!)
                main_theme_dd = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "dd[field='ZYZT'][tit='主要主题']"))
                )

                # --- 关键修改点 2: 取消之前选中的主题 ---
                print(f"准备选择主题 '{theme_name}'，先取消其他已选主题...")
                # 重新查找所有复选框 (关键!)
                checkbox_inputs = main_theme_dd.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                
                for input_tag in checkbox_inputs:
                    value = input_tag.get_attribute("value")
                    if not value:
                        continue

                    # 如果这个复选框是选中的，并且它的value不是我们即将要选的主题名
                    if input_tag.is_selected():
                        if value != theme_name:
                            print(f"  取消选中主题 '{value}'")
                            # 点击它来取消选中
                            driver.execute_script("arguments[0].click();", input_tag)
                            # --- 关键修改点 3: 点击后等待并重新定位 ---
                            time.sleep(0.5) # 等待 DOM 更新
                            # 重新定位主要区域和复选框列表，因为 DOM 可能已变
                            main_theme_dd = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "dd[field='ZYZT'][tit='主要主题']"))
                            )
                        else:
                            # 如果要选的主题已经被选中了，也先取消，再重新选，确保触发搜索
                            print(f"  目标主题 '{value}' 已选中，先取消再重新选中以确保触发搜索")
                            driver.execute_script("arguments[0].click();", input_tag)
                            time.sleep(0.5)
                            main_theme_dd = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "dd[field='ZYZT'][tit='主要主题']"))
                            )
                
                # 等待一小会儿，让取消操作生效
                time.sleep(0.5)

                # --- 关键修改点 4: 选中目标主题 ---
                # 再次重新查找所有复选框，确保获取到最新的列表
                checkbox_inputs = main_theme_dd.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                target_checkbox = None
                for input_tag in checkbox_inputs:
                    value = input_tag.get_attribute("value")
                    if value == theme_name:
                        target_checkbox = input_tag
                        break

                if target_checkbox:
                    print(f"正在点击主题 '{theme_name}' 的复选框...")
                    driver.execute_script("arguments[0].click();", target_checkbox)
                    
                    # 等待结果刷新
                    time.sleep(1) 
                    
                    # --- 关键修改点 5: 爬取数据 ---
                    for page in range(1, MAX_PAGES_PER_THEME + 1):
                        print(f"正在爬取主题 '{theme_name}' 第 {page} 页...")
                        try:
                            # 等待表格加载或更新
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".result-table-list tbody tr"))
                            )
                            # 获取当前页面的数据
                            table_rows = driver.find_elements(By.CSS_SELECTOR, ".result-table-list tbody tr")
                            for row in table_rows:
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if len(cells) >= 5:
                                    title_cell = cells[1]  # 题名
                                    author_cell = cells[2]  # 作者
                                    source_cell = cells[3]  # 来源
                                    date_cell = cells[4]  # 发表时间
                                    db_cell = cells[5]  # 数据库

                                    title = title_cell.text.strip()
                                    authors = author_cell.text.strip()
                                    source = source_cell.text.strip()
                                    publish_time = date_cell.text.strip()
                                    database = db_cell.text.strip()

                                    data.append({
                                        "题名": title,
                                        "作者": authors,
                                        "来源": source,
                                        "发表时间": publish_time,
                                        "数据库": database,
                                        "主题": theme_name
                                    })

                            # --- 关键修改点 6: 翻页 ---
                            try:
                                # 等待下一页按钮状态更新
                                next_button = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, "//a[@class='next']"))
                                )
                                # 检查是否禁用
                                if "disabled" in next_button.get_attribute("class") or "javascript:void(0)" in next_button.get_attribute("href"):
                                    print("  已到最后一页")
                                    break
                                print("  点击下一页")
                                next_button.click()
                                # 等待新页面加载
                                time.sleep(2) 

                            except TimeoutException:
                                print("  未找到可点击的下一页按钮，可能已到最后一页")
                                break

                        except Exception as e:
                            print(f"第 {page} 页出错或超时: {e}")
                            continue

                else:
                    print(f"错误：在主要主题区域未找到名为 '{theme_name}' 的复选框")

                # 如果能执行到这里，说明本次尝试成功，跳出重试循环
                break

            except StaleElementReferenceException as e:
                print(f"  (尝试 {attempt + 1}/{max_retries}) 遇到 StaleElementReferenceException: {e}")
                if attempt == max_retries - 1:
                    # 如果是最后一次尝试，仍然失败，则抛出异常
                    raise
                else:
                    # 否则，等待一下再重试
                    print("  等待 1 秒后重试...")
                    time.sleep(1)
                    continue # 继续下一次 for 循环

    except Exception as e:
        print(f"爬取主题 '{theme_name}' 失败: {e}")
        import traceback
        traceback.print_exc()

    return data

# =============================
# 保存到 CSV
# =============================
def save_to_csv(data, filename):
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["题名", "作者", "来源", "发表时间", "数据库", "主题"])
        writer.writeheader()
        writer.writerows(data)
    print(f"已保存 {len(data)} 条记录到 {filename}")

# =============================
# 主程序
# =============================
def main():
    driver = setup_driver()
    try:
        # 打开知网首页
        url = "https://www.cnki.net/"
        driver.get(url)
        time.sleep(3)

        # --- 新增：先设置筛选条件 ---
        print("正在设置筛选条件，只保留'学术期刊'和'会议'...")
        # 定义要保留的选项 ID (根据你之前的分析)
        keep_options = ["CJFQ", "CIPD"]  # CJFQ=学术期刊, CIPD=会议

        # 查找所有选项的 li 元素
        # 等待选项列表加载
        wait = WebDriverWait(driver, 10)
        all_options = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.option-list ul li"))
        )
        # 或者使用 find_elements，如果你确定它会加载
        # all_options = driver.find_elements(By.CSS_SELECTOR, "div.option-list ul li")

        for option in all_options:
            # 获取其 id 属性
            option_id = option.get_attribute("id")
            if not option_id:
                continue

            # 检查当前状态
            is_selected = "selected" in option.get_attribute("class")
            should_be_selected = option_id in keep_options

            # 如果状态不对，则点击它
            if is_selected and not should_be_selected:
                print(f"  取消选中: {option_id}")
                driver.execute_script("arguments[0].click();", option)
            elif not is_selected and should_be_selected:
                print(f"  勾选: {option_id}")
                driver.execute_script("arguments[0].click();", option)

        # 等待一下，让操作生效
        time.sleep(1)
        print("筛选条件设置完成。")

        # --- 继续搜索流程 ---
        # 等待并找到搜索框
        search_box = wait_until_visible(driver, By.ID, "txt_SearchText")

        # 输入关键词
        search_box.clear()
        search_box.send_keys(SEARCH_KEYWORD)

        # 找到并点击搜索按钮
        search_btn = driver.find_element(By.CLASS_NAME, "search-btn")
        search_btn.click()

        # --- 等待搜索结果加载 ---
        # 等待搜索结果加载完成 (调整为实际结果列表的定位符)
        wait_until_visible(driver, By.ID, "gridTable")
        print("已跳转到搜索结果页，结果列表已加载")

        # --- 后续流程不变 ---
        # 获取所有主题
        themes = get_themes(driver)
        print(f"共找到 {len(themes)} 个主题:")
        for t in themes:
            print(f"  - {t['name']} ({t['count']}篇)")

        # 依次爬取每个主题
        all_data = []
        for theme in themes:
            print(f"\n开始爬取主题: {theme['name']}")
            data = crawl_by_theme(driver, theme['name'])
            all_data.extend(data)
            print(f"完成，共获取 {len(data)} 条")

            # 保存为独立 CSV 文件
            filename = os.path.join(OUTPUT_DIR, f"{theme['name'].replace(' ', '_')}.csv")
            save_to_csv(data, filename)

        # 合并所有数据（可选）
        combined_filename = os.path.join(OUTPUT_DIR, "all_results.csv")
        save_to_csv(all_data, combined_filename)

    except Exception as e:
        print(f"程序异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    main()