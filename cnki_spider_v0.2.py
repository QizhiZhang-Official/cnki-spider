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
            
    time.sleep(5)


def main():
    # 初始化浏览器
    driver = setup_driver()
    
    # 打开知网首页
    url = "https://www.cnki.net/"
    driver.get(url)
    time.sleep(3)
    
    options_filter(driver)


if __name__ == '__main__':
    main()