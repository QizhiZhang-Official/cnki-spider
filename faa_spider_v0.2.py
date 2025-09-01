import codecs
import requests
from bs4 import BeautifulSoup
import time
import csv
import urllib.parse
from datetime import datetime, timedelta
import os

# ================= 配置参数 =================
# 注意：URL 末尾的空格已被移除以确保正确性
BASE_URL = "https://www.faa.gov/newsroom/press_releases"
ARCHIVE_URL = "https://www.faa.gov/newsroom/news_archive"
SEARCH_PARAMS = {
    'keys': 'drone',
    'field_region_target_id': 'All'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
}

DELAY = 2  # 请求之间的延迟（秒）
# 使用当前工作目录保存文件
CURRENT_PATH = os.getcwd()
OUTPUT_FILE = os.path.join(CURRENT_PATH, 'faa_drone_press_releases.csv')
MAX_PAGES_CURRENT = 10  # 限制爬取当前新闻的最大页数
MAX_PAGES_ARCHIVE = 10  # 限制爬取存档新闻的最大页数
UPDATE_MODE = True  # 运行模式：True 为增量更新，False 为全量爬取

def get_article_data(link):
    """获取单个新闻详情页的内容"""
    try:
        # 使用 urljoin 安全地处理相对链接
        full_link = urllib.parse.urljoin(BASE_URL, link) if not link.startswith('http') else link
        response = requests.get(full_link, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取发布日期
        date_div = soup.select_one('div.mb-4')
        pub_date = date_div.get_text(strip=True) if date_div else "Unknown"

        # 提取新闻正文内容
        content_div = soup.select_one('div.mb-4.clearfix')
        if not content_div:
            content = "No content found."
        else:
            children = content_div.children
            content_lines = []
            for child in children:
                # 仅提取指定的标签内容
                if child.name and child.name in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    text = child.get_text(strip=False)
                    if text.strip():
                        content_lines.append(text)
            content = '\n\n'.join(content_lines)
            content = content.replace('\n\n\n', '\n\n')

        return pub_date, content

    except Exception as e:
        print(f"   [错误] 无法获取文章详情 {full_link}: {e}")
        return "Error", "Failed to retrieve content"


def scrape_news_list(base_url, search_params, max_pages, description):
    """通用函数：爬取指定URL的新闻列表"""
    articles = []
    page = 0
    has_next = True

    print(f"[开始] 正在爬取 {description}...")

    while has_next and (max_pages is None or page < max_pages):
        # 为每一页请求复制参数，避免修改原始参数
        params = search_params.copy()
        if page > 0:
            params['page'] = page

        list_url = base_url + '?' + urllib.parse.urlencode(params)
        print(f"[进度] 正在获取 {description} 第 {page + 1} 页: {list_url}")

        try:
            response = requests.get(list_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找新闻条目
            entries = soup.select('.views-row')

            if not entries:
                print(f"[提示] 在 {description} 未找到更多新闻条目，可能已到最后一页。")
                break

            print(f"[成功] 在 {description} 第 {page + 1} 页找到 {len(entries)} 条新闻。")

            for entry in entries:
                title_elem = entry.select_one('.views-field-title a')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                href = title_elem['href']
                # 使用 urljoin 构建完整的新闻链接
                link = urllib.parse.urljoin(base_url, href)

                print(f"   [详情] 正在抓取: {title}")
                pub_date, content = get_article_data(link)
                articles.append({
                    'title': title,
                    'date': pub_date,
                    'url': link,
                    'content': content
                })

                # 遵守延迟设置
                time.sleep(DELAY)

            # 检查是否存在下一页
            has_next = False
            next_btn_debug_info = "未找到下一页按钮"

            # 方法 1: 查找具有 'pager__item--next' 类的 li 元素
            next_li = soup.select_one('li.pager__item--next')
            if next_li:
                # 在该 li 元素中查找 a 标签
                next_a_in_li = next_li.find('a')
                if next_a_in_li and next_a_in_li.get('href'):
                    has_next = True
                    next_btn_debug_info = f"找到 (通过 pager__item--next > a[href], href='{next_a_in_li['href']}')"
                else:
                    next_btn_debug_info = "找到 pager__item--next 的 li，但其内部的 a 标签无效或无 href"
            else:
                next_btn_debug_info = "未找到 pager__item--next 的 li"

            # 如果方法 1 失败，尝试方法 2: 查找具有 rel='next' 属性的 a 标签
            if not has_next:
                next_a_rel = soup.find('a', rel='next')
                if next_a_rel and next_a_rel.get('href'):
                    has_next = True
                    next_btn_debug_info = f"找到 (通过 rel='next', href='{next_a_rel['href']}')"
                else:
                    next_btn_debug_info = next_btn_debug_info + " | 未找到 rel='next' 的 a 标签"

            # 如果方法 2 也失败，尝试方法 3: 查找文本为 'Next ›' 或 'Next' 的 a 标签
            if not has_next:
                 next_a_text1 = soup.find('a', string='Next ›')
                 if next_a_text1 and next_a_text1.get('href'):
                     has_next = True
                     next_btn_debug_info = f"找到 (通过文本 'Next ›', href='{next_a_text1['href']}')"
                 else:
                     next_btn_debug_info = next_btn_debug_info + " | 未找到文本为 'Next ›' 的 a 标签"

            if not has_next:
                 next_a_text2 = soup.find('a', string='Next')
                 if next_a_text2 and next_a_text2.get('href'):
                     has_next = True
                     next_btn_debug_info = f"找到 (通过文本 'Next', href='{next_a_text2['href']}')"
                 else:
                     next_btn_debug_info = next_btn_debug_info + " | 未找到文本为 'Next' 的 a 标签"

            print(f"   [分页] {next_btn_debug_info}")
            # --- 修改后的分页判断逻辑结束 ---

            page += 1
            time.sleep(DELAY)

        except requests.exceptions.RequestException as e:
            print(f"   [网络错误] 请求失败 {list_url}: {e}")
            # 遇到网络错误时停止爬取
            has_next = False
        except Exception as e:
            print(f"   [未知错误] 处理页面时发生错误 {list_url}: {e}")
            # 遇到其他错误时停止爬取
            has_next = False

    print(f"[完成] {description} 爬取完毕，共获取 {len(articles)} 篇新闻。")
    return articles


def scrape_faa_press_releases():
    """主函数：执行 FAA 新闻稿爬取任务"""
    global UPDATE_MODE, SEARCH_PARAMS
    all_articles = []

    # --- 日期解析配置 ---
    # 定义可能遇到的日期格式，以提高代码的健壮性
    DATE_FORMATS = [
        '%A, %B %d, %Y',  # 格式: Thursday, August 7, 2025
        '%B %d, %Y',      # 格式: August 7, 2025
        # 可根据需要添加更多格式
    ]

    # === 增量更新模式：读取已有数据，获取最新日期 ===
    latest_date = None

    if UPDATE_MODE and os.path.exists(OUTPUT_FILE):
        print("[模式] 检测到增量更新模式，正在读取现有数据以确定最新日期...")
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    article_date_str = row.get('date', '').strip()
                    # 跳过无效或占位符日期
                    if not article_date_str or article_date_str.lower() in ("unknown", "error"):
                        continue

                    date_obj = None
                    # 尝试使用多种格式解析日期
                    for fmt in DATE_FORMATS:
                        try:
                            date_obj = datetime.strptime(article_date_str, fmt)
                            break  # 解析成功则跳出循环
                        except ValueError:
                            continue  # 尝试下一种格式

                    if date_obj is None:
                        print(f"   [警告] 无法解析日期，已跳过: {row.get('title', 'N/A')} - 日期: '{article_date_str}'")
                        continue

                    # 更新最新日期
                    if latest_date is None or date_obj > latest_date:
                        latest_date = date_obj

            if latest_date:
                # --- 核心逻辑修正 ---
                # 计算下一天，确保只获取更新的内容，避免重复抓取
                next_day = latest_date + timedelta(days=1)
                # 使用 FAA 网站正确的参数名设置日期筛选
                SEARCH_PARAMS['field_effective_date_value'] = next_day.strftime('%Y-%m-%d')
                SEARCH_PARAMS['field_effective_date_value_1'] = ''  # 结束日期通常留空
                print(f"[设置] 增量更新已配置，将从 {next_day.strftime('%Y-%m-%d')} 之后开始抓取。")
            else:
                print("[警告] 现有文件中未找到有效日期，将切换至全量爬取模式。")
                UPDATE_MODE = False
        except Exception as e:
            print(f"[错误] 读取文件 {OUTPUT_FILE} 时发生错误: {e}")
            print("[警告] 将切换至全量爬取模式。")
            UPDATE_MODE = False
    else:
        mode_desc = "增量模式" if UPDATE_MODE else "全量模式"
        file_status = "不存在" if UPDATE_MODE else ""
        print(f"[模式] 当前为 {mode_desc} ({'文件 ' + OUTPUT_FILE + ' ' + file_status if UPDATE_MODE else '已指定'})，将进行全量爬取。")
        # 确保在全量爬取模式下不携带日期筛选参数
        SEARCH_PARAMS.pop('field_effective_date_value', None)
        SEARCH_PARAMS.pop('field_effective_date_value_1', None)

    # === 爬取当前新闻 (Press Releases) ===
    print("\n--- 开始爬取当前新闻 ---")
    current_articles = scrape_news_list(BASE_URL, SEARCH_PARAMS, MAX_PAGES_CURRENT, "当前新闻 (Press Releases)")
    all_articles.extend(current_articles)

    # === 爬取历史新闻 (News Archive) ===
    print("\n--- 开始爬取历史新闻 ---")
    # 存档页也支持相同的搜索参数
    archive_params = SEARCH_PARAMS.copy()
    archive_articles = scrape_news_list(ARCHIVE_URL, archive_params, MAX_PAGES_ARCHIVE, "历史新闻 (News Archive)")
    all_articles.extend(archive_articles)

    # === 数据合并与保存 ===
    print("\n--- 数据处理与保存 ---")
    # 根据新闻链接 (URL) 去重
    unique_articles = list({a['url']: a for a in all_articles}.values())
    print(f"[去重] 本次抓取去重后，获得 {len(unique_articles)} 篇新闻。")

    final_articles = unique_articles
    if UPDATE_MODE and os.path.exists(OUTPUT_FILE):
        print("[合并] 增量更新模式：正在将新数据与现有数据合并...")
        existing_articles = []
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                existing_articles = list(reader)
            print(f"[加载] 已加载 {len(existing_articles)} 篇现有新闻。")

            # 合并旧数据和新数据 (URL 作为唯一键)
            all_articles_dict = {a['url']: a for a in existing_articles}  # 先加载旧数据
            for new_article in unique_articles:  # 再更新或添加新数据
                all_articles_dict[new_article['url']] = new_article

            final_articles = list(all_articles_dict.values())
            print(f"[合并] 数据合并完成，总计 {len(final_articles)} 篇唯一新闻。")
        except Exception as e:
            print(f"[警告] 读取现有文件时出错: {e}。将只保存本次抓取的新数据。")

    # 确保输出目录存在
    output_dir = os.path.dirname(OUTPUT_FILE)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 将最终结果写入 CSV 文件
    try:
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'date', 'url', 'content'])
            writer.writeheader()
            writer.writerows(final_articles)
        print(f"[成功] 爬取任务完成！共保存 {len(final_articles)} 篇唯一新闻稿至 {OUTPUT_FILE}")
    except Exception as e:
        print(f"[致命错误] 无法写入文件 {OUTPUT_FILE}: {e}")


if __name__ == '__main__':
    scrape_faa_press_releases()
