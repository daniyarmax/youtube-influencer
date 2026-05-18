# 📊 YouTube Influencer Analytics

> A Python-based research tool that collects, cleans, and analyzes YouTube channel & video data via the YouTube Data API v3 — designed for influencer market research in the **tech devices and computer peripherals** niche.

---

## 🗂️ Project Overview

This project automates the full pipeline of YouTube influencer research:

1. **Collects** channel and video data from YouTube Data API v3
2. **Parses** descriptions for advertising signals, external links, and social platform presence
3. **Cleans** raw data in Google Colab notebooks
4. **Stores** results in SQL with analytical views
5. **Visualizes** insights via Tableau / Looker Studio dashboards

---

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| Data Collection | Python, YouTube Data API v3, `google-api-python-client` |
| Parsing & Scraping | `BeautifulSoup4`, `requests`, `lxml` |
| Data Processing | `pandas`, `numpy` |
| Data Cleaning | Google Colab |
| Database & Analytics | PostgreSQL / SQL (views, window functions) |
| Export Formats | CSV, JSON, Excel (`.xlsx`) |
| Visualization | Tableau, Looker Studio |
| Environment | `python-dotenv`, `openpyxl` |

---

## 📁 Project Structure

```
Youtube analytics/
│
├── parsing scripts/
│   ├── main.py            # Entry point — runs the full collection pipeline
│   ├── api_client.py      # YouTube Data API v3 wrapper (channel & video fetching)
│   ├── parser.py          # Content analysis: ad keywords, links, social platforms
│   ├── analytics.py       # Computes channel-level aggregate metrics
│   ├── exporter.py        # Saves output to CSV / Excel / JSON
│   ├── utils.py           # URL extraction, domain detection, helper functions
│   ├── config.py          # Keywords, domains, API settings, output filenames
│   ├── requirements.txt   # Python dependencies
│   └── output/
│       ├── channels.csv
│       ├── channels.json
│       ├── videos.csv
│       ├── videos.json
│       ├── summary_report.csv
│       └── youtube_research.xlsx
│
├── data cleaning/
│   ├── YoutubeInfluencser-channeltable.ipynb   # Channel data cleaning notebook
│   └── Youtube-influencer-videos-table.ipynb   # Video data cleaning notebook
│
├── data/
│   ├── raw/               # Original collected data
│   │   ├── channels.csv
│   │   └── videos.csv
│   └── cleaned/           # Processed data ready for SQL import
│       ├── channels_cleaned.numbers
│       └── videos_cleaned_new.csv
│
├── sql/
│   ├── queries/
│   │   ├── create.sql     # Table definitions + view creation
│   │   └── query.sql      # Analytical queries
│   └── views/             # Exported SQL view results
│       ├── channel_analytics.csv
│       ├── video_features.csv
│       ├── video_features_enhanced.csv
│       ├── video_cadence.csv
│       └── video_performance_relative.csv
│
└── dashboards/
    ├── channel_dashboard.png
    └── video_dashboard.png
```

---

## ⚙️ How It Works

### 1. Data Collection (`parsing scripts/`)

The pipeline is triggered from `main.py`. It accepts a list of YouTube channel URLs or handles and:

- Resolves channel handles/custom URLs to internal channel IDs via the API
- Fetches channel metadata (subscribers, total views, country, creation date)
- Retrieves the latest N videos (default: 50) per channel
- Fetches per-video statistics: views, likes, comments, duration, tags

**Ad & Link Detection (`parser.py`)** scans channel and video descriptions for:

- Ad/sponsorship keywords in Russian and English (`реклама`, `sponsor`, `promo code`, etc.)
- Marketplace/store links (`amazon.com`, `ozon.ru`, `wildberries.ru`, etc.)
- Social platform presence: Instagram, Telegram, TikTok, VK, Twitter/X, Facebook, Discord

**Metrics Computation (`analytics.py`)** calculates per-channel aggregates:

- Average views, likes, comments (last 50 videos)
- Engagement rate: `(likes + comments) / views`
- Upload frequency: videos per week

**Export (`exporter.py`)** writes results to:

- `channels.csv` / `videos.csv` / `summary_report.csv`
- `youtube_research.xlsx` (multi-sheet: Channels, Videos, Summary, README)
- `channels.json` / `videos.json`

---

### 2. Data Cleaning (`data cleaning/`)

Colab notebooks handle:
- Removing duplicates and nulls
- Standardizing data types and column formats
- Preparing tables for SQL import

---

### 3. SQL Analytics (`sql/`)

**Table schema** includes: `videos` (video_id, channel_id, title, published_at, duration_seconds, view_count, like_count, comment_count, is_short, has_ad_keywords, external_links, etc.)

**SQL Views created:**

| View | Description |
|------|-------------|
| `channel_analytics` | Per-channel aggregates: avg views, engagement rate, Shorts share, ad video share, publishing velocity, views-per-subscriber efficiency |
| `video_features` | Per-video enriched features including engagement rate, monetization type, publish day/hour |
| `video_features_enhanced` | Adds log-transformed metrics (`log_views`, `log_likes`, `log_comments`) |
| `video_performance_relative` | Compares each video to its channel average — labels videos as `outperformer`, `normal`, or `underperformer` |
| `video_cadence` | Days between consecutive uploads per channel using `LAG()` window function |

**Example analytical queries included:**
```sql
-- Channels that overperform relative to subscriber count
SELECT channel_title, subscriber_count, avg_views_per_video,
       avg_views_per_video_per_subscriber, avg_engagement_rate
FROM channel_analytics
ORDER BY avg_views_per_video_per_subscriber DESC;

-- Shorts vs. long-form performance
SELECT is_short, COUNT(*) AS videos,
       AVG(view_count) AS avg_views,
       AVG(engagement_rate) AS avg_engagement_rate
FROM video_features
GROUP BY is_short;

-- Best publishing days and hours
SELECT publish_dow, COUNT(*) AS videos, AVG(view_count) AS avg_views
FROM video_features
GROUP BY publish_dow ORDER BY publish_dow;
```

---

### 4. Dashboards

| Dashboard | Preview |
|-----------|---------|
| Channel Analytics | `dashboards/channel_dashboard.png` |
| Video Performance | `dashboards/video_dashboard.png` |

Built in **Tableau** and **Looker Studio** to visualize engagement trends, channel efficiency scores, and monetization patterns.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A YouTube Data API v3 key ([get one here](https://console.cloud.google.com/))

### 1. Clone the Repository

```bash
git clone https://github.com/daniyarmax/youtube-influencer.git
cd youtube-influencer/Youtube\ analytics/parsing\ scripts
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up API Key

Create a `.env` file in the `parsing scripts/` folder:

```env
YOUTUBE_API_KEY=your_api_key_here
```

### 4. Configure Channels

Edit the `CHANNEL_INPUTS` list in `main.py`:

```python
CHANNEL_INPUTS = [
    "https://www.youtube.com/@Wylsacom",
    "https://www.youtube.com/@rozetked",
    # add more channels...
]
```

### 5. Run the Pipeline

```bash
python main.py

# Optional flags:
python main.py --max-videos 30 --output-dir ./results --no-excel
```

Output files will appear in the `output/` folder.

---

## 💡 Key Insights

- High subscriber counts don't guarantee high engagement — mid-sized creators often outperform large channels on a views-per-subscriber basis
- Sponsored/ad videos show measurable differences in engagement vs. organic content
- Publishing cadence (day of week, hour) correlates with view performance
- YouTube Shorts and long-form videos serve different audience interaction patterns

---

## 🔮 Future Improvements

- [ ] Add `.env` setup guide and API quota management
- [ ] Automate SQL import step (load CSV → PostgreSQL)
- [ ] Build a Streamlit dashboard for interactive exploration
- [ ] Add ML-based engagement prediction
- [ ] Extend niche coverage beyond tech/peripherals

---

## 👤 Author

**Daniyar Maksut**

[![GitHub](https://img.shields.io/badge/GitHub-daniyarmax-181717?style=flat&logo=github)](https://github.com/daniyarmax)

---

## 📄 License

This project is open source and intended for educational and research purposes.
