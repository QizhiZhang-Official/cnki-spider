import requests
import time
import platform
import subprocess

def is_network_connected(host="www.baidu.com", timeout=3):
    """
    使用系统 ping 命令检测网络连通性。
    返回 True 表示能 ping 通，False 表示不通。
    """
    # 根据操作系统选择参数
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_param = "-w" if platform.system().lower() == "windows" else "-W"

    try:
        # Windows: ping -n 1 -w 3000 www.baidu.com
        # Linux/macOS: ping -c 1 -W 3 www.baidu.com
        if platform.system().lower() == "windows":
            # Windows 的 -w 单位是毫秒
            result = subprocess.run(
                ["ping", param, "1", timeout_param, str(timeout * 1000), host],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # Linux/macOS 的 -W 单位是秒
            result = subprocess.run(
                ["ping", param, "1", timeout_param, str(timeout), host],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return result.returncode == 0
    except Exception:
        return False

# 请根据实际情况调整参数
url = "http://192.168.100.200/drcom/login"

params = {
    "callback": "dr1003",
    "DDDDD": "2024022251",        # 你的账号
    "upass": "055313@gtm",      # 你的密码 (注意这里用了冒号，不是@)
    "0MKKey": "123456",           # 固定值
    "R1": "0",
    "R2": "8",
    "R3": "0",
    "R6": "0",
    "para": "00",
    "v6ip": "",
    "terminal_type": "1",
    "lang": "zh-cn",
    "jsVersion": "4.1.3",
    "v": "10057"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Referer": "http://192.168.100.200/",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Connection": "keep-alive"
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=10)
    print("状态码:", response.status_code)
    print("响应头:", response.headers)
    print("响应内容 (前 500 字符):")
    print(response.text[:500])
except Exception as e:
    print("请求失败:", e)


# 使用示例
if is_network_connected("www.baidu.com"):
    print("恭喜！你已成功登录校园网。")
else:
    print("登录失败，或者网络未连接。")