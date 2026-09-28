# cnki-faa-spider

**cnki-faa-spider** 是一套面向"低空经济"研究主题的文献与新闻数据采集工具集，基于 Python 实现，包含两个相互独立的数据采集模块：面向中国知网（CNKI）的学术文献爬虫，以及面向美国联邦航空管理局（FAA）官网的无人机相关新闻稿爬虫。

## 目录

- [项目结构](#项目结构)
- [环境要求](#环境要求)
- [安装](#安装)
- [使用说明](#使用说明)
- [输出说明](#输出说明)
- [注意事项](#注意事项)
- [版权声明](#版权声明)

## 项目结构

```text
cnki-faa-spider/
├── src/
│   ├── cnki_spider.py        # CNKI 文献爬虫（Selenium 实现）
│   ├── cnki_spider_clean.py  # CNKI 文献爬虫（精简版，功能一致）
│   └── faa_spider.py         # FAA 无人机新闻稿爬虫（requests + BeautifulSoup 实现）
├── output/                   # 数据输出目录
├── msedgedriver.exe          # Edge 浏览器驱动（需按本机 Edge 内核版本自行配置）
├── pyproject.toml            # 项目依赖配置
├── uv.lock                   # 依赖锁定文件
├── LICENSE                   # Apache License 2.0
└── README.md
```

### 模块概览

| 模块 | 数据源 | 技术方案 | 输出文件 |
|------|--------|----------|----------|
| `cnki_spider.py` | 中国知网（CNKI） | Selenium + Edge 浏览器自动化 | `output/cnki.csv` |
| `faa_spider.py` | FAA 官网新闻中心 | requests + BeautifulSoup | `faa_drone_press_releases.csv` |

## 环境要求

- **Python** ≥ 3.14
- **Microsoft Edge 浏览器**（CNKI 爬虫依赖）
- **Microsoft Edge WebDriver（msedgedriver.exe）**：版本必须与本机 Edge 浏览器内核版本一致
- **uv**（推荐）或 pip，用于依赖管理

### 获取匹配版本的 msedgedriver.exe

WebDriver 与浏览器内核版本必须严格对应，否则 Selenium 将无法启动浏览器。请按以下步骤获取：

1. 确认本机 Edge 内核版本：打开 Edge，访问 `edge://settings/help`，页面顶部显示的即为当前版本号（如 `128.0.2739.79`）。
2. 前往微软官方下载页 <https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/>，下载与该版本号**完全一致**的 msedgedriver。
3. 将解压得到的 `msedgedriver.exe` 置于项目根目录下（与脚本中的默认路径保持一致）。

> 项目根目录中附带的 `msedgedriver.exe` 仅对应特定 Edge 版本。若运行时报错 `session not created: This version of msedgedriver only supports Microsoft Edge XX`，说明驱动版本与浏览器不匹配，请按上述步骤替换为本机对应版本的驱动。

## 安装

推荐使用 [uv](https://docs.astral.sh/uv/) 管理依赖：

```bash
uv sync
```

或使用 pip：

```bash
pip install beautifulsoup4 pandas requests selenium
```

## 使用说明

### 1. CNKI 文献爬虫

该模块通过 Selenium 模拟浏览器操作，自动完成以下流程：打开知网首页 → 按关键词检索 → 勾选数据库范围（默认仅"学术期刊"与"会议"）→ 展开并遍历"主要主题"分类 → 逐主题抓取文献条目，并逐条进入详情页获取摘要。

运行前请在 `src/cnki_spider.py` 的 `main()` 函数中确认以下配置：

```python
SEARCH_KEY = '低空经济'   # 检索关键词
NEXT_PAGE = False         # True: 抓取全部页 / False: 仅抓取首页（每页 50 条）
SAVE_NAME = 'cnki.csv'    # 输出文件名
```

如需调整数据库范围（如纳入学位论文、报纸等），请修改 `options_filter()` 函数中的 `options` 字典；如需浏览器在后台静默运行，请取消 `setup_driver()` 中 `--headless` 一行的注释。

执行：

```bash
python src/cnki_spider.py
```

### 2. FAA 无人机新闻稿爬虫

该模块基于 HTTP 请求实现，同时抓取 FAA 官网"当前新闻（Press Releases）"与"历史存档（News Archive）"两个栏目中关键词 "drone" 相关的新闻稿，并支持增量更新与全量抓取两种模式。

运行前请在 `src/faa_spider.py` 顶部确认以下配置：

```python
SEARCH_PARAMS = {'keys': 'drone', ...}  # 检索关键词
MAX_PAGES_CURRENT = 10                  # 当前新闻最大抓取页数
MAX_PAGES_ARCHIVE = 10                  # 历史存档最大抓取页数
UPDATE_MODE = True                      # True: 增量更新 / False: 全量抓取
DELAY = 2                               # 请求间隔（秒）
```

- **增量更新模式**（默认）：自动读取已有 CSV 中的最新发布日期，仅抓取其后新增的新闻，并与既有数据按 URL 去重合并；
- **全量抓取模式**：从零开始抓取全部符合条件的内容并覆盖写入。

执行：

```bash
python src/faa_spider.py
```

## 输出说明

| 文件 | 内容 | 字段 |
|------|------|------|
| `output/cnki.csv` | 知网文献数据 | theme（主题）、name（标题）、author（作者）、abstract（摘要）、source（来源）、date（发表日期）、database（所属数据库）、quote（被引次数）、download（下载次数） |
| `faa_drone_press_releases.csv` | FAA 新闻稿数据 | title（标题）、date（发布日期）、url（链接）、content（正文） |

所有 CSV 均采用 UTF-8-SIG 编码，可直接使用 Excel 打开，中文内容不会出现乱码。

## 注意事项

1. **页面结构依赖**：知网检索结果由 JavaScript 动态渲染，若网站改版，脚本中的 CSS 选择器可能需要相应更新。
2. **抓取耗时**：CNKI 摘要需逐条进入详情页获取，全量抓取耗时较长，请耐心等待并避免中途关闭浏览器。
3. **合规使用**：请合理控制抓取频率，遵守目标网站的服务条款与 robots 协议。本项目仅供学术研究和个人学习使用，使用者需自行承担数据使用产生的相关责任。

## 版权声明

Copyright © 2026 张启知（Qizhi Zhang）<Qizhi-Zhang@outlook.com>

本项目采用 [Apache License 2.0](LICENSE) 开源协议授权。任何人在遵守该协议条款的前提下，可自由使用、复制、修改及分发本项目，但须保留本版权声明及许可证副本，并对自行修改的部分作出显著标注。本项目按"现状"（AS IS）提供，不附带任何形式的明示或默示保证。
