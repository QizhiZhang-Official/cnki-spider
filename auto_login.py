from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

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

def login_with_iframe(driver, account, password):
    wait = WebDriverWait(driver, 15)

    try:
        # 1. 等待页面加载完成
        print("🔍 等待页面加载...")
        wait.until(EC.title_contains("连接到网络"))

        # 2. 查找并等待 iframe 出现
        print("🔍 等待 iframe 加载...")
        iframe = wait.until(
            EC.presence_of_element_located((By.NAME, "c"))
        )
        print("✅ iframe 已找到")

        # 3. 切换到 iframe
        print("🔄 正在切换到 iframe...")
        driver.switch_to.frame(iframe)
        print("✅ 已切换到 iframe")

        # 4. 等待登录表单元素出现（根据你提供的 HTML）
        print("🔍 等待账号输入框...")
        account_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='DDDDD']"))
        )
        print("✅ 账号输入框已找到")

        print("🔍 等待密码输入框...")
        password_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='upass']"))
        )
        print("✅ 密码输入框已找到")

        # 5. 填写账号密码
        account_input.clear()
        account_input.send_keys(account)
        print("✅ 账号已填写")

        password_input.clear()
        password_input.send_keys(password)
        print("✅ 密码已填写")

        # 6. 点击登录按钮
        print("🔍 等待登录按钮...")
        login_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='0MKKey']"))
        )
        login_btn.click()
        print("✅ 已点击登录按钮")

        # 7. 等待登录结果
        time.sleep(3)
        print("当前 URL:", driver.current_url)

    except TimeoutException as e:
        print("❌ 超时异常！可能是 iframe 未加载或元素未找到")
        print("当前页面源码片段：")
        print(driver.page_source[:500])
        raise
    except Exception as e:
        print("❌ 其他异常:", str(e))
        raise

def main():
    account = '2024022251'
    password = '055313@gtm'

    driver = setup_driver()
    driver.get("https://192.168.100.200/")

    print("当前 URL:", driver.current_url)
    print("页面标题:", driver.title)

    login_with_iframe(driver, account, password)

    driver.quit()

if __name__ == '__main__':
    main()