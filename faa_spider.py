import requests
from bs4 import BeautifulSoup
import time
import csv
import urllib.parse

# ================= 配置参数 =================
BASE_URL = "https://www.faa.gov/newsroom/press_releases"
SEARCH_PARAMS = {
    'keys': 'drone',
    'field_region_target_id': 'All'
}

# 请求头：伪装成浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
}

# 延迟设置（秒），避免请求过快
DELAY = 5

# 输出文件
OUTPUT_FILE = 'faa_drone_press_releases.csv'

# 最大页数限制（防止无限翻页，可设为 None 表示不限）
MAX_PAGES = 10  # FAA 页面一般不会太多页，10 足够
# ============================================


def get_article_data(link):
    """获取单个新闻详情页的内容"""
    try:
        response = requests.get(link, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取正文（常见 class: .field-name-body 或 .article-body）
        content_elem = soup.select_one('.field-name-body')
        content = content_elem.get_text(strip=True) if content_elem else "No content found."

        # 提取发布日期（通常在 .date-display-single）
        date_elem = soup.select_one('.date-display-single')
        pub_date = date_elem.get('content') if date_elem else "Unknown"

        return pub_date, content
    except Exception as e:
        print(f"   ❌ 获取详情失败 {link}: {e}")
        return "Error", "Failed to retrieve content"


def scrape_faa_press_releases():
    """主函数：爬取所有 drone 相关新闻稿"""
    articles = []
    page = 0
    has_next = True

    print("🚀 开始爬取 FAA 新闻稿...")

    while has_next and (MAX_PAGES is None or page < MAX_PAGES):
        # 构造分页 URL
        params = SEARCH_PARAMS.copy()
        if page > 0:
            params['page'] = page

        list_url = BASE_URL + '?' + urllib.parse.urlencode(params)
        print(f"\n📌 正在获取第 {page + 1} 页: {list_url}")

        try:
            response = requests.get(list_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找所有新闻条目（标题链接）
            entries = soup.select('.view-content .card-title a')

            if not entries:
                print("   🛑 未找到新闻条目，可能已到最后一页。")
                break

            print(f"   ✅ 找到 {len(entries)} 条新闻，开始抓取详情...")

            for entry in entries:
                title = entry.get_text(strip=True)
                href = entry['href']
                link = f"https://www.faa.gov{href}"

                print(f"   📄 正在抓取: {title}")
                pub_date, content = get_article_data(link)
                articles.append({
                    'title': title,
                    'date': pub_date,
                    'url': link,
                    'content': content
                })

                time.sleep(DELAY)  # 每抓一个详情页暂停

            # 判断是否有下一页（检查“Next”按钮）
            next_btn = soup.find('a', text='›')
            has_next = bool(next_btn)

            page += 1
            time.sleep(DELAY)  # 每翻一页暂停

        except Exception as e:
            print(f"   ❌ 请求失败 {list_url}: {e}")
            has_next = False

    # 保存结果
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'date', 'url', 'content'])
        writer.writeheader()
        writer.writerows(articles)

    print(f"\n✅ 爬取完成！共获取 {len(articles)} 篇新闻稿，已保存至 {OUTPUT_FILE}")


# =================== 运行脚本 ===================
if __name__ == '__main__':
    scrape_faa_press_releases()