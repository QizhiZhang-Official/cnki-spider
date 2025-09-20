import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.edge.options import Options as EdgeOptions


def setup_driver():
    edge_options = EdgeOptions()
    edge_options.add_argument("--start-maximized")  # 启动时最大化窗口
    edge_options.add_argument("--disable-extensions")  # 禁用浏览器扩展
    edge_options.add_argument("--disable-gpu")  # 禁用 GPU 加速
    edge_options.add_argument("--no-sandbox")  # 禁用沙盒模式（某些系统需要）
    edge_options.add_argument("--disable-dev-shm-usage")  # 避免内存共享问题

    # 如果你希望浏览器在后台运行（不显示界面），可以取消下面这行的注释
    # edge_options.add_argument('--headless')
    
    service = Service(executable_path=os.path.join(os.getcwd(), 'msedgedriver.exe'))

    driver = webdriver.Edge(service=service, options=edge_options)
    
    return driver


def open_url(driver, url):
    driver.get(url)
    time.sleep(1)


def options_filter(driver):
    options = {
        'CJFQ': True,   # 学术期刊
        'CDMD': False,  # 学位论文
        'CIPD': True,   # 会议
        'CCND': False,  # 报纸
        'CYFD': False,  # 年鉴
        'SCOD': False,  # 专利
        'CISD': False,  # 标准
        'SNAD': False,  # 成果
        'CCJD': False,  # 学术辑刊
        'BDZK': False,  # 图书
        'WENKU': False  # 文库
    }
    
    for id in options:
        option = driver.find_element(By.ID, id)
        is_selected = "selected" in option.get_attribute("class")

        if is_selected != options[id]:
            option.find_element(By.TAG_NAME, "i").click()

    time.sleep(1)


def search(driver, search_key):
    search_txt = driver.find_element(By.ID, "txt_SearchText")
    search_txt.send_keys(search_key)

    search_btn = driver.find_element(By.CLASS_NAME, "search-btn")
    search_btn.click()

    time.sleep(1)


def get_all_themes(driver):
    main_themes = driver.find_element("css selector", "dd[tit='主要主题']")
    
    btn = main_themes.find_element("css selector", "a[class='btn']")
    btn.click()
    
    themes = main_themes.find_elements("css selector", "ul > li > input")
    
    themes_list = []
    for theme in themes:
        themes_list.append(theme.accessible_name)

    return themes_list


def get_data_by_themes(driver, themes, next_page):
    all_data_df = pd.DataFrame()
    
    display_select = driver.find_element("css selector", "div[class='statistic']")
    display_select = display_select.find_element("css selector", "div[class='sort']")
    display_select.click()

    display_50 = driver.find_element("css selector", "li[data-val='50'] a")
    display_50.click()
    
    time.sleep(1)

    for theme in themes:
        main_themes = driver.find_element("css selector", "dd[tit='主要主题']")
        checkbox = main_themes.find_element("css selector", f"input[value='{theme}']")
        more_btn = main_themes.find_element("css selector", "a.btn")

        if (theme != themes[0]):
            more_btn.click()
        
        checkbox.click()
        time.sleep(1)

        while True:
            data = driver.find_element("css selector", "table[class='result-table-list']")
            data = data.find_element("css selector", "tbody")

            # 1. 标题 (name)
            name_element = data.find_elements("css selector", "a[class='fz14']")
            name_list = []
            for name in name_element:
                name_list.append(name.text)
            
            # 2. 作者 (author)
            author_element = data.find_elements("css selector", "td[class='author']")
            author_list = []
            for author in author_element:
                author_list.append(author.text)
            
            # 3. 来源 (source)
            source_element = data.find_elements("css selector", "td[class='source']")
            source_list = []
            for source in source_element:
                source_list.append(source.text)
            
            # 4. 发表日期 (date)
            date_element = data.find_elements("css selector", "td[class='date']")
            date_list = []
            for date in date_element:
                date_list.append(date.text)
            
            # 5. 数据库 (database)
            database_element = data.find_elements("css selector", "td[class='data']")
            database_list = []
            for database in database_element:
                database_list.append(database.text)
            
            # 6. 被引次数 (quote)
            quote_element = data.find_elements("css selector", "td[class='quote']")
            quote_list = []
            for quote in quote_element:
                quote_list.append(quote.text)
            
            # 7. 下载次数 (download)
            download_element = data.find_elements("css selector", "td[class='download']")
            download_list = []
            for download in download_element:
                download_list.append(download.text)
            
            # 8. 摘要 (abstract)
            abstract_list = []
            for name in name_element:
                name.click()
                time.sleep(1)

                driver.switch_to.window(driver.window_handles[-1])

                try:
                    doc = driver.find_element("css selector", "div[class='doc']")
                    abstract = doc.find_element("css selector", "span[class='abstract-text']")
                    abstract_list.append(abstract.text)
                except NoSuchElementException:
                    abstract_list.append("")

                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            
            data_df = pd.DataFrame({
                'theme': [theme] * len(name_list),
                'name': name_list,
                'author': author_list,
                'abstract': abstract_list,
                'source': source_list,
                'date': date_list,
                'database': database_list,
                'quote': quote_list,
                'download': download_list
            })
            all_data_df = pd.concat([all_data_df, data_df], ignore_index=True)
            
            if next_page:
                try:
                    pages = driver.find_element("css selector", "div[class=pages]")
                    next_page = pages.find_element("css selector", "a[class=pagesnums]")
                    next_page.click()
                    time.sleep(1)
                    continue
                except NoSuchElementException:
                    break
            else:
                break
        
        main_themes = driver.find_element("css selector", "dd[tit='主要主题']")
        checkbox = main_themes.find_element("css selector", f"input[value='{theme}']")
        checkbox.click()
        
        time.sleep(1)
        
    return all_data_df


def save_data(data, save_dir, save_name):
    os.makedirs(save_dir, exist_ok=True)
    data.to_csv(os.path.join(save_dir, save_name), encoding='utf-8-sig', index=False)


def main():
    # 路径配置
    SAVE_DIR = os.path.join(os.getcwd(), 'output')  # 保存的路径
    SAVE_NAME = 'cnki.csv'  # 保存的文件名
    # 爬虫配置
    URL = 'https://www.cnki.net/'
    SEARCH_KEY = '低空经济'
    NEXT_PAGE = False
    
    # 初始化浏览器
    driver = setup_driver()
    # 打开知网首页
    open_url(driver, URL)
    # 筛选搜索选项
    options_filter(driver)
    # 使用关键词搜索
    search(driver, SEARCH_KEY)
    # 获取所有主题分类
    themes = get_all_themes(driver)
    # 获取所有数据
    data = get_data_by_themes(driver, themes, NEXT_PAGE)
    # 保存
    save_data(data, SAVE_DIR, SAVE_NAME)


if __name__ == '__main__':
    main()