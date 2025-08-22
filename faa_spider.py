import codecs
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
}

DELAY = 2
OUTPUT_FILE = 'faa_drone_press_releases.csv'
MAX_PAGES = 10  # 最大翻页数

def get_article_data(link):
    """获取单个新闻详情页的内容"""
    try:
        response = requests.get(link, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # ✅ 提取日期
        date_div = soup.select_one('div.mb-4')
        pub_date = date_div.get_text(strip=True) if date_div else "Unknown"

        # ✅ 提取正文：只处理 mb-4.clearfix 的直接子元素
        content_div = soup.select_one('div.mb-4.clearfix')
        if not content_div:
            content = "No content found."
        else:
            # 获取所有直接子元素（包括 p, h3, ul, etc.）
            children = content_div.children
            content_lines = []
            for child in children:
                if child.name:  # 确保是标签元素（不是文本节点）
                    text = child.get_text(strip=False)  # 保留原始空格和换行
                    if text.strip():
                        content_lines.append(text)

            content = '\n\n'.join(content_lines)
            
            content = content.replace('\n\n\n', '\n\n')

        return pub_date, content

    except Exception as e:
        print(f"   ❌ 获取详情失败 {link}: {e}")
        return "Error", "Failed to retrieve content"


def scrape_faa_press_releases():
    articles = []
    page = 0
    has_next = True

    print("🚀 开始爬取 FAA 新闻稿...")

    while has_next and (MAX_PAGES is None or page < MAX_PAGES):
        params = SEARCH_PARAMS.copy()
        if page > 0:
            params['page'] = page

        list_url = BASE_URL + '?' + urllib.parse.urlencode(params)
        print(f"\n📌 正在获取第 {page + 1} 页: {list_url}")

        try:
            response = requests.get(list_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # ✅ 重点修改：正确选择每个新闻条目
            entries = soup.select('.views-row')

            if not entries:
                print("   🛑 未找到新闻条目，可能已到最后一页。")
                break

            print(f"   ✅ 找到 {len(entries)} 条新闻，开始抓取详情...")

            for entry in entries:
                # 提取标题和链接
                title_elem = entry.select_one('.views-field-title a')
                if not title_elem:
                    continue  # 跳过无标题项

                title = title_elem.get_text(strip=True)
                href = title_elem['href']
                link = f"https://www.faa.gov{href}"

                print(f"   📄 正在抓取: {title}")
                pub_date, content = get_article_data(link)
                articles.append({
                    'title': title,
                    'date': pub_date,
                    'url': link,
                    'content': content
                })

                time.sleep(DELAY)

            # 判断是否有下一页
            next_btn = soup.find('a', string='›')
            has_next = bool(next_btn)

            page += 1
            time.sleep(DELAY)

        except Exception as e:
            print(f"   ❌ 请求失败 {list_url}: {e}")
            has_next = False

    # 保存结果
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        with codecs.open(OUTPUT_FILE, 'w', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'date', 'url', 'content'])
            writer.writeheader()
            writer.writerows(articles)

    print(f"\n✅ 爬取完成！共获取 {len(articles)} 篇新闻稿，已保存至 {OUTPUT_FILE}")


if __name__ == '__main__':
    scrape_faa_press_releases()