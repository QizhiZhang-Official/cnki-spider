# -*- coding: utf-8 -*-
"""
这是一个用于从中国知网 (CNKI) 爬取特定主题（例如“低空经济”）下文献信息的程序。
使用了 Selenium 库来模拟浏览器操作，因为知网的内容是通过 JavaScript 动态加载的。
"""

# 导入程序运行所需的库
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.edge.options import Options as EdgeOptions


# ----------------------------
# 函数定义区域
# ----------------------------
def setup_driver():
    """
    初始化并返回一个配置好的 Edge 浏览器驱动对象。
    这个函数会设置浏览器的启动参数，比如最大化窗口、禁用插件等，
    并指定浏览器驱动的位置（msedgedriver.exe）。
    """
    # 创建一个 EdgeOptions 对象，用来设置浏览器选项
    edge_options = EdgeOptions()
    edge_options.add_argument("--start-maximized")  # 启动时最大化窗口
    edge_options.add_argument("--disable-extensions")  # 禁用浏览器扩展
    edge_options.add_argument("--disable-gpu")  # 禁用 GPU 加速
    edge_options.add_argument("--no-sandbox")  # 禁用沙盒模式（某些系统需要）
    edge_options.add_argument("--disable-dev-shm-usage")  # 避免内存共享问题

    # 如果你希望浏览器在后台运行（不显示界面），可以取消下面这行的注释
    # edge_options.add_argument('--headless')

    # 指定浏览器驱动的路径（浏览器驱动就是项目根目录中的 msedgedriver.exe）
    service = Service(executable_path=os.path.join(os.getcwd(), 'msedgedriver.exe'))

    # 创建并返回一个 Edge 浏览器驱动实例
    driver = webdriver.Edge(service=service, options=edge_options)
    
    return driver


def open_url(driver, url):
    """
    使用浏览器驱动打开指定的网址，并等待1秒让页面加载。
    
    Args:
        driver: 已经初始化好的浏览器驱动对象。
        url (str): 要打开的网页地址。
    """
    # 让浏览器访问指定的网址
    driver.get(url)
    # 等待1秒，确保页面有足够时间开始加载
    time.sleep(1)


def options_filter(driver):
    """
    在知网首页，选择或取消选择特定的文献数据库。
    这里我只选择了“学术期刊”(CJFQ) 和“会议”(CIPD) 数据库。
    之后根据需要修改。
    """
    # 定义一个字典，键是数据库的 ID，值是是否要选中它 (True 表示选中)
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
    
    # 遍历字典中的每一个选项
    for id in options:
        # 在网页上找到对应 ID 的元素
        option = driver.find_element(By.ID, id)
        # 检查该选项当前是否被选中（通过检查 class 属性中是否包含 "selected"）
        is_selected = "selected" in option.get_attribute("class")

        # 如果当前选中状态和我们期望的不一致，则点击它来切换状态
        if is_selected != options[id]:
            # 点击选项内的 <i> 标签来切换选中状态
            option.find_element(By.TAG_NAME, "i").click()

    # 等待 1 秒，让页面有时间响应筛选操作
    time.sleep(1)


def search(driver, search_key):
    """
    在搜索框中输入指定的关键词，然后点击搜索按钮。
    
    Args:
        driver: 已经初始化好的浏览器驱动对象。
        search_key (str): 要搜索的关键词。
    """
    # 找到搜索框元素（通过 ID "txt_SearchText"）
    search_txt = driver.find_element(By.ID, "txt_SearchText")
    # 在搜索框中输入指定的关键词
    search_txt.send_keys(search_key)

    # 找到搜索按钮（通过 class name "search-btn"）
    search_btn = driver.find_element(By.CLASS_NAME, "search-btn")
    # 点击搜索按钮
    search_btn.click()

    # 等待 1 秒，让页面跳转和加载搜索结果
    time.sleep(1)


def get_all_themes(driver):
    """
    在搜索结果页面，展开“主要主题”筛选项，并获取所有可用的主题分类名称。
    """
    # 找到“主要主题”这一筛选项的容器（通过 CSS 选择器）
    main_themes = driver.find_element("css selector", "dd[tit='主要主题']")
    
    # 找到“更多”按钮并点击，以展开所有主题选项
    btn = main_themes.find_element("css selector", "a[class='btn']")
    btn.click()
    
    # 找到所有主题的复选框（<input> 元素）
    themes = main_themes.find_elements("css selector", "ul > li > input")
    
    # 创建一个空列表来存储主题名称
    themes_list = []
    # 遍历所有复选框，获取它们的名称（accessible_name）并添加到列表中
    for theme in themes:
        themes_list.append(theme.accessible_name)

    # 返回包含所有主题名称的列表
    return themes_list


def get_data_by_themes(driver, themes, next_page):
    """
    根据给定的主题列表，依次筛选并爬取每个主题下的文献数据。
    
    Args:
        driver: 已经初始化好的浏览器驱动对象。
        themes (list): 包含所有要爬取的主题名称的列表。
        is_next_page: 是否爬取多页数据。如果为 False，则只爬取第一页。
        
    Returns:
        pd.DataFrame: 包含所有爬取到的数据的 DataFrame。
    """
    # 创建一个空的 DataFrame 来存储最终的所有数据
    all_data_df = pd.DataFrame()
    
    # --- 修改一页显示的最大文献数量为 50 ---
    # 找到页面上控制显示数量的下拉菜单
    display_select = driver.find_element("css selector", "div[class='statistic']")
    display_select = display_select.find_element("css selector", "div[class='sort']")
    display_select.click()  # 点击下拉菜单

    # 找到“每页显示 50 条”的选项并点击
    display_50 = driver.find_element("css selector", "li[data-val='50'] a")
    display_50.click()
    time.sleep(1)  # 等待页面刷新

    # --- 遍历每一个主题进行数据爬取 ---
    for theme in themes:
        print(f"正在爬取主题: {theme}")  # 在控制台打印当前主题，方便观察进度

        # 重新找到“主要主题”筛选项的容器
        main_themes = driver.find_element("css selector", "dd[tit='主要主题']")
        # 找到当前主题对应的复选框
        checkbox = main_themes.find_element("css selector", f"input[value='{theme}']")
        # 找到“更多”按钮
        more_btn = main_themes.find_element("css selector", "a.btn")

        # 如果不是第一个主题（列表中的第一个元素），需要先点击“更多”按钮才能看到其他复选框
        if (theme != themes[0]):
            more_btn.click()
        # 点击当前主题的复选框，应用筛选
        checkbox.click()
        time.sleep(1)  # 等待筛选结果加载

        # --- 开始爬取当前主题下的所有页面数据 ---
        while True:  # 这个循环会处理当前主题的所有分页
            # 找到包含文献列表的表格
            data = driver.find_element("css selector", "table[class='result-table-list']")
            data = data.find_element("css selector", "tbody")  # 找到表格主体

            # --- 提取表格中的各项信息 ---
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
            
            # 8. 摘要 (abstract) - 需要点击标题进入详情页获取
            abstract_list = []
            # 遍历当前页的每一个标题链接
            for name in name_element:
                name.click()  # 点击标题链接
                time.sleep(1)  # 等待新页面加载

                # 切换到新打开的标签页（窗口）
                driver.switch_to.window(driver.window_handles[-1])

                # 在新页面中找到摘要文本
                try:
                    # 尝试找到摘要所在的元素
                    doc = driver.find_element("css selector", "div[class='doc']")
                    abstract = doc.find_element("css selector", "span[class='abstract-text']")
                    abstract_list.append(abstract.text)
                except NoSuchElementException:
                    # 如果没找到摘要（例如页面结构不同），就添加一个空字符串
                    abstract_list.append("")

                # 关闭当前标签页
                driver.close()
                # 切换回原来的搜索结果页面
                driver.switch_to.window(driver.window_handles[0])
                    
            # --- 将提取的数据合并成一个 DataFrame ---
            # 使用字典创建一个临时 DataFrame
            data_df = pd.DataFrame({
                'theme': [theme] * len(name_list),  # 为每一行数据都添加当前主题
                'name': name_list,
                'author': author_list,
                'abstract': abstract_list,
                'source': source_list,
                'date': date_list,
                'database': database_list,
                'quote': quote_list,
                'download': download_list
            })
            # 将临时 DataFrame 添加到总的数据 DataFrame 中
            all_data_df = pd.concat([all_data_df, data_df], ignore_index=True)
            
            # --- 如果 next_page 为 True，则检查并处理下一页 ---
            if next_page:
                try:
                    # 找到分页导航区域
                    pages = driver.find_element("css selector", "div[class=pages]")
                    # 找到“下一页”按钮
                    next_page = pages.find_element("css selector", "a[class=pagesnums]")
                    # 点击“下一页”按钮
                    next_page.click()
                    time.sleep(1)  # 等待新页面加载
                    # 继续 while 循环，处理下一页
                    continue
                except NoSuchElementException:
                    # 如果找不到“下一页”按钮，说明已经是最后一页了
                    # 跳出 while 循环，处理下一个主题
                    break
            else:
                # 如果 is_next_page 为 False，跳出 while 循环，处理下一个主题
                break
        
        # --- 完成当前主题的爬取后，取消该主题的筛选 ---
        main_themes = driver.find_element("css selector", "dd[tit='主要主题']")
        checkbox = main_themes.find_element("css selector", f"input[value='{theme}']")
        checkbox.click()  # 再次点击复选框取消筛选
        time.sleep(1)  # 等待页面刷新
    
    # 返回包含所有爬取数据的 DataFrame
    return all_data_df


def save_data(data, save_dir, save_name):
    """
    将爬取到的数据保存为 CSV 文件。
    
    Args:
        data (pd.DataFrame): 要保存的数据。
        save_dir (str): 保存文件的目录路径。
        save_name (str): 保存的文件名（应包含 .csv 扩展名）。
    """
    # 确保保存数据的目录存在，如果不存在则自动创建
    os.makedirs(save_dir, exist_ok=True)
    # 将数据保存为 CSV 文件，使用 utf-8-sig 编码以正确显示中文
    data.to_csv(os.path.join(save_dir, save_name), encoding='utf-8-sig', index=False)


def main():
    # 0.0 路径配置
    SAVE_DIR = os.path.join(os.getcwd(), 'output')  # 保存的路径
    SAVE_NAME = 'cnki.csv'  # 保存的文件名
    # 0.1 爬虫配置
    URL = 'https://www.cnki.net/'  # 知网的链接
    SEARCH_KEY = '低空经济'  # 搜索的关键词
    NEXT_PAGE = False  # True: 爬取所有页数 / False: 只爬取第一页
    
    
    # 1. 初始化浏览器
    driver = setup_driver()
    # 2. 打开知网首页
    open_url(driver, URL)
    # 3. 筛选搜索选项
    options_filter(driver)
    # 4. 使用关键词搜索
    search(driver, SEARCH_KEY)
    # 5. 获取所有主题分类
    themes = get_all_themes(driver)
    # 6. 
    
    # 7. 获取所有数据
    data = get_data_by_themes(driver, themes, NEXT_PAGE)
    # 8. 保存
    save_data(data, SAVE_DIR, SAVE_NAME)


# ----------------------------
# 程序入口
# ----------------------------

# 这行代码是 Python 的标准写法，确保只有直接运行此脚本时，main() 函数才会被执行。
# 如果这个文件被其他文件导入，则 main() 不会自动运行。
if __name__ == '__main__':
    main()