import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options as EdgeOptions


def setup_driver():
    edge_options = EdgeOptions()
    edge_options.add_argument("--start-maximized")
    edge_options.add_argument("--disable-extensions")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")

    service = Service(executable_path=r'./msedgedriver.exe')

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
    for theme in themes:
        main_themes = driver.find_element("css selector", "dd[tit='主要主题']")
        checkbox = main_themes.find_element("css selector", f"input[value='{theme}']")
        checkbox.click()
        time.sleep(1)
        
        data = driver.find_element("css selector", "table[class='result-table-list']")
        data = data.find_element("css selector", "tbody")
        name_element = data.find_elements("css selector", "a[class='fz14']")
        name_list = []
        for name in name_element:
            name_list.append(name.text)
        print(name_list)
        
        main_themes = driver.find_element("css selector", "dd[tit='主要主题']")
        checkbox = main_themes.find_element("css selector", f"input[value='{theme}']")
        checkbox.click()
        time.sleep(1)
    
    


def main():
    # 初始化浏览器
    driver = setup_driver()
    
    # 打开知网首页
    url = "https://www.cnki.net/"
    driver.get(url)
    time.sleep(3)
    
    options_filter(driver)
    
    search(driver)
    
    themes = get_all_themes(driver)
    
    get_data_by_themes(driver, themes)


if __name__ == '__main__':
    main()