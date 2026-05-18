"""
config.py — Project configuration: keywords, domains, and constants.
"""

# ── Advertising / commercial keywords to search in descriptions ──────────────
AD_KEYWORDS_RU = [
    "сотрудничество", "реклама", "промокод", "партнёрство",
    "скидка", "купон", "ссылка в описании", "акция",
]

AD_KEYWORDS_EN = [
    "sponsor", "sponsored", "partnership", "collaboration",
    "affiliate", "referral", "discount", "coupon",
    "buy here", "link in description", "use code", "promo code",
    "paid promotion", "ad", "advertisement",
]

ALL_AD_KEYWORDS = AD_KEYWORDS_RU + AD_KEYWORDS_EN

# ── Store / marketplace domains to detect in links ───────────────────────────
STORE_DOMAINS = [
    "amazon.com", "amazon.co", "amzn.to",
    "aliexpress.com", "aliexpress.ru",
    "dns-shop.ru", "citilink.ru", "mvideo.ru",
    "wildberries.ru", "ozon.ru", "eldorado.ru",
    "bestbuy.com", "newegg.com", "bhphotovideo.com",
    "ebay.com", "shop.apple.com",
]

# ── Social / external platform patterns ──────────────────────────────────────
SOCIAL_PLATFORMS = {
    "instagram":  ["instagram.com"],
    "telegram":   ["t.me", "telegram.me"],
    "tiktok":     ["tiktok.com"],
    "vk":         ["vk.com", "vk.ru"],
    "twitter_x":  ["twitter.com", "x.com"],
    "facebook":   ["facebook.com", "fb.com"],
    "discord":    ["discord.gg", "discord.com/invite"],
}

# ── API / request settings ────────────────────────────────────────────────────
MAX_VIDEOS_DEFAULT = 50
REQUEST_DELAY_SEC  = 0.5   # polite delay between HTTP requests
REQUEST_TIMEOUT    = 15    # seconds

# ── Output file names ────────────────────────────────────────────────────────
OUT_CHANNELS_CSV      = "channels.csv"
OUT_VIDEOS_CSV        = "videos.csv"
OUT_SUMMARY_CSV       = "summary_report.csv"
OUT_EXCEL             = "youtube_research.xlsx"
OUT_JSON_CHANNELS     = "channels.json"
OUT_JSON_VIDEOS       = "videos.json"

NICHE_LABEL = "Tech devices and computer peripherals"
