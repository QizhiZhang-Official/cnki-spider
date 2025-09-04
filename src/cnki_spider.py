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
    edge_options.add_argument("--start-maximized")
    edge_options.add_argument("--disable-extensions")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    # edge_options.add_argument('--headless')

    service = Service(executable_path=os.path.join(os.getcwd(), 'msedgedriver.exe'))

    driver = webdriver.Edge(service=service, options=edge_options)
    
    return driver


def options_filter(driver):
    options = {
        'CJFQ': True,
        'CDMD': False,
        'CIPD': True,
        'CCND': False,
        'CYFD': False,
        'SCOD': False,
        'CISD': False,
        'SNAD': False,
        'CCJD': False,
        'BDZK': False,
        'WENKU': False
    }
    
    for id in options:
        option = driver.find_element(By.ID, id)
        is_selected = "selected" in option.get_attribute("class")
        
        if is_selected == options[id]:
            pass
        else:
            option.find_element(By.TAG_NAME, "i").click()
            
    time.sleep(1)


def search(driver):
    search_txt = driver.find_element(By.ID, "txt_SearchText")
    search_txt.send_keys("低空经济")
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


def get_data_by_themes(driver, themes):
    all_data_df = pd.DataFrame()
    
    # 修改一页最大显示数量为 50
    display_select = driver.find_element("css selector", "div[class='statistic']")
    display_select = display_select.find_element("css selector", "div[class='sort']")
    display_select.click()
    display_50 = driver.find_element("css selector", "li[data-val='50'] a")
    display_50.click()
    time.sleep(1)
    
    # 按照主题分类依次爬取
    for theme in themes:
        main_themes = driver.find_element("css selector", "dd[tit='主要主题']")
        checkbox = main_themes.find_element("css selector", f"input[value='{theme}']")
        more_btn = main_themes.find_element("css selector", "a.btn")
        if (theme != '低空经济'):
            more_btn.click()
        checkbox.click()
        time.sleep(1)
        
        # 爬取这一页的所有数据，若有下一页则循环
        while True:
            data = driver.find_element("css selector", "table[class='result-table-list']")
            data = data.find_element("css selector", "tbody")
            
            # name
            name_element = data.find_elements("css selector", "a[class='fz14']")
            name_list = []
            for name in name_element:
                name_list.append(name.text)
            
            # author
            author_element = data.find_elements("css selector", "td[class='author']")
            author_list = []
            for author in author_element:
                author_list.append(author.text)
            
            # source
            source_element = data.find_elements("css selector", "td[class='source']")
            source_list = []
            for source in source_element:
                source_list.append(source.text)
            
            # date
            date_element = data.find_elements("css selector", "td[class='date']")
            date_list = []
            for date in date_element:
                date_list.append(date.text)
            
            # database
            database_element = data.find_elements("css selector", "td[class='data']")
            database_list = []
            for database in database_element:
                database_list.append(database.text)
            
            # quote
            quote_element = data.find_elements("css selector", "td[class='quote']")
            quote_list = []
            for quote in quote_element:
                quote_list.append(quote.text)
            
            # download
            download_element = data.find_elements("css selector", "td[class='download']")
            download_list = []
            for download in download_element:
                download_list.append(download.text)
            
            # abstract
            abstract_list = []
            for name in name_element:
                name.click()
                time.sleep(1)
                driver.switch_to.window(driver.window_handles[-1])
                
                doc = driver.find_element("css selector", "div[class='doc']")
                abstract = doc.find_element("css selector", "span[class='abstract-text']")
                abstract_list.append(abstract.text)
                
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                    
            # 合并所有元素
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
            
            break
            
            # 判断是否有下一页
            try:
                pages = driver.find_element("css selector", "div[class=pages]")
                next_page = pages.find_element("css selector", "a[class=pagesnums]")
                next_page.click()
                time.sleep(1)
                continue
            except NoSuchElementException:
                break
        
        main_themes = driver.find_element("css selector", "dd[tit='主要主题']")
        checkbox = main_themes.find_element("css selector", f"input[value='{theme}']")
        checkbox.click()
        time.sleep(1)
    
    return all_data_df


def main():
    # 初始化浏览器
    driver = setup_driver()
    
    # 打开知网首页
    url = "https://www.cnki.net/"
    driver.get(url)
    time.sleep(1)
    
    # 筛选搜索选项
    options_filter(driver)
    
    # 搜索
    search(driver)
    
    # 获取所有主题分类
    themes = get_all_themes(driver)
    
    # 获取所有数据
    data = get_data_by_themes(driver, themes)
    
    # 保存
    data.to_csv(os.path.join(os.getcwd(), 'output', 'cnki.csv'), encoding='utf-8-sig', index=False)


if __name__ == '__main__':
    main()