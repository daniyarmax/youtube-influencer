# YouTube Tech Channel Research Tool

Collects and analyses data from 30–50 YouTube channels in the **tech devices and peripherals** niche using the official YouTube Data API v3.

---

## Architecture overview

```
main.py          ← orchestrates the full pipeline
├── api_client.py   ← YouTube Data API v3 wrapper (channel + video data)
├── parser.py       ← content analysis: ad keywords, links, social platforms
├── analytics.py    ← aggregate metrics: avg views, engagement rate, upload freq
├── exporter.py     ← saves results to CSV / Excel / JSON
├── config.py       ← keywords, domains, constants
└── utils.py        ← URL parsing, duration conversion, link extraction
```

### Data flow

```
Channel URL / ID
      ↓
[api_client] resolve → channel ID
      ↓
[api_client] channels.list → channel metadata
      ↓
[api_client] playlistItems.list → latest N video IDs
      ↓
[api_client] videos.list → video stats + descriptions
      ↓
[parser]     analyse_channel_text → ad keywords, social links, store domains
      ↓
[analytics]  compute_channel_metrics → avg views, engagement, upload freq
      ↓
[exporter]   save CSV / Excel / JSON
```

---

## Folder structure

```
youtube_research/
├── main.py              ← entry point (edit CHANNEL_INPUTS here)
├── api_client.py        ← API wrapper
├── parser.py            ← content analysis + optional scraping
├── analytics.py         ← metrics computation
├── exporter.py          ← file export
├── config.py            ← keywords, domains, settings
├── utils.py             ← shared helpers
├── requirements.txt
├── .env.example         ← template — copy to .env
├── .env                 ← your real API key (never commit this!)
├── research.log         ← created at runtime
└── output/              ← created at runtime
    ├── channels.csv
    ├── videos.csv
    ├── summary_report.csv
    ├── youtube_research.xlsx
    ├── channels.json
    └── videos.json
```

---

## Setup

### 1. Clone / download the project

```bash
cd youtube_research
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your API key

```bash
cp .env.example .env
# Open .env and paste your YouTube Data API v3 key
```

### 5. Add your channels

Open `main.py` and edit the `CHANNEL_INPUTS` list.
You can use any of these formats:

```python
CHANNEL_INPUTS = [
    "https://www.youtube.com/@LinusTechTips",   # @handle URL
    "https://www.youtube.com/channel/UCxxxxxx", # /channel/ URL
    "UCxxxxxxxxxxxxxxxxxxxxxx",                  # bare channel ID
    "https://www.youtube.com/c/CustomName",     # /c/ custom name
]
```

---

## Usage

### Basic run (50 videos per channel, output to ./output)

```bash
python main.py
```

### Custom number of videos

```bash
python main.py --max-videos 30
```

### Custom output directory

```bash
python main.py --output-dir ./my_results
```

### With optional About page scraping

```bash
python main.py --scrape
```

### Skip Excel / JSON export

```bash
python main.py --no-excel --no-json
```

### Full example

```bash
python main.py --max-videos 50 --output-dir ./results --scrape
```

---

## Output files

### channels.csv

One row per channel. Columns include:

| Column | Source | Description |
|--------|--------|-------------|
| channel_id | API | YouTube channel ID |
| channel_title | API | Channel name |
| niche | static | Always "Tech devices and computer peripherals" |
| subscriber_count | API | Subscriber count |
| total_views | API | Total channel views |
| video_count | API | Total videos published |
| country | API | Country code (if available) |
| published_at | API | Channel creation date |
| description | API | Channel description text |
| has_ad_keywords | Parsed | Any advertising keywords found |
| matched_ad_keywords | Parsed | Which keywords were found (pipe-separated) |
| has_affiliate_signals | Parsed | Affiliate/referral signals detected |
| has_marketplace_links | Parsed | Store or marketplace links found |
| has_instagram / has_telegram / ... | Parsed | Social platform detected |
| ecosystem_detected | Parsed | Creator has external ecosystem |
| external_links_count | Parsed | Total external URLs in descriptions |
| matched_store_domains | Parsed | Which store domains were found |

### videos.csv

One row per video. Columns include:

| Column | Source | Description |
|--------|--------|-------------|
| channel_id | API | Parent channel ID |
| video_id | API | YouTube video ID |
| video_url | API | Full video URL |
| title | API | Video title |
| published_at | API | Publication date |
| duration | API | Human-readable duration (e.g. "12m 34s") |
| duration_seconds | API | Duration in seconds |
| view_count | API | View count |
| like_count | API | Like count |
| comment_count | API | Comment count |
| tags | API | Tags (pipe-separated) |
| description | API | Video description |
| has_ad_keywords | Parsed | Ad keywords in this video's description |
| matched_ad_keywords | Parsed | Which ad keywords were found |
| has_external_links | Parsed | Any external URLs in description |
| external_links | Parsed | Found URLs (pipe-separated, max 20) |

### summary_report.csv

One row per channel — channel metadata + computed metrics:

| Column | Description |
|--------|-------------|
| avg_views_last_50 | Average views across fetched videos |
| avg_likes_last_50 | Average likes |
| avg_comments_last_50 | Average comments |
| engagement_rate_estimate | (likes + comments) / views, averaged |
| upload_frequency_estimate | Estimated uploads per week |
| proportion_videos_with_ad_signals | Share of videos with ad keywords |
| proportion_videos_with_external_links | Share of videos with external links |

---

## API quota notes

The YouTube Data API v3 gives you **10,000 units per day** on the free tier.

| Operation | Units per call | Calls for 50 channels × 50 videos |
|-----------|---------------|-----------------------------------|
| channels.list (metadata) | 1 | 50 |
| playlistItems.list (video IDs, 1 page) | 1 | ~50 |
| videos.list (50 IDs per call) | 1 | ~50 |
| **Total** | | **~150–200 units** |

50 channels × 50 videos ≈ **150–250 units total** — well within the free daily quota.

`search.list` costs **100 units per call** — this project avoids it entirely.

---

## YouTube scraping limitations

YouTube is a JavaScript Single-Page Application (SPA). Plain HTTP requests
return mostly empty HTML — the actual content is loaded by JavaScript after page load.

| Data | API | Plain HTTP scrape | Selenium/Playwright |
|------|-----|-------------------|---------------------|
| Channel metadata | ✅ Full | ❌ Meta tags only | ✅ Full |
| Subscriber count | ✅ | ❌ | ✅ |
| Video list | ✅ | ❌ | ✅ |
| About page links | ✅ (in description) | ❌ JS-rendered | ✅ |
| Video descriptions | ✅ | ❌ | ✅ |

**This project uses the official API for all primary data.**
The `--scrape` flag adds a best-effort HTTP scrape that may extract
`<meta>` tag content but will miss most dynamic content.

---

## Русская инструкция (краткое руководство по запуску)

### Что нужно сделать:

1. **Установить Python 3.10+** с официального сайта python.org

2. **Скачать проект** и перейти в папку:
   ```bash
   cd youtube_research
   ```

3. **Создать виртуальное окружение** и активировать его:
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   # или
   source venv/bin/activate  # macOS/Linux
   ```

4. **Установить зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Получить API-ключ:**
   - Перейти на https://console.cloud.google.com/
   - Создать проект → включить "YouTube Data API v3"
   - Credentials → Create Credentials → API Key
   - Скопировать файл `.env.example` в `.env` и вставить ключ

6. **Добавить каналы** в список `CHANNEL_INPUTS` в файле `main.py`

7. **Запустить сбор данных:**
   ```bash
   python main.py
   ```

8. **Результаты** появятся в папке `./output/`:
   - `channels.csv` — данные по каналам
   - `videos.csv` — данные по видео
   - `summary_report.csv` — сводные метрики
   - `youtube_research.xlsx` — Excel-файл с тремя листами
   - `channels.json` / `videos.json` — JSON-экспорт

Логи выполнения пишутся в файл `research.log` и выводятся в консоль.
