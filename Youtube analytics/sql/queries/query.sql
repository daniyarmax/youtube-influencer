create table videos(
	channel_id TEXT,
    video_id TEXT PRIMARY KEY,
    video_url TEXT,
    title TEXT,
    published_at TIMESTAMP,
    duration TEXT,
    duration_seconds INTEGER,
    tags TEXT,
    description TEXT,
    view_count BIGINT,
    like_count BIGINT,
    comment_count BIGINT,
    has_ad_keywords BOOLEAN,
    matched_ad_keywords TEXT,
    has_external_links BOOLEAN,
    external_links_count INTEGER,
    external_links TEXT,
    is_short BOOLEAN
);

select * from video_features;

CREATE OR REPLACE VIEW channel_analytics AS
WITH video_base AS (
    SELECT
        v.channel_id,
        COUNT(*) AS videos_in_dataset,
        SUM(v.view_count) AS dataset_views,
        AVG(v.view_count)::numeric(18,2) AS avg_views_per_video,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY v.view_count) AS median_views_per_video,
        MAX(v.view_count) AS max_views,
        MIN(v.view_count) AS min_views,

        AVG(v.like_count::numeric / NULLIF(v.view_count, 0)) AS avg_like_rate,
        AVG(v.comment_count::numeric / NULLIF(v.view_count, 0)) AS avg_comment_rate,
        AVG((v.like_count + v.comment_count)::numeric / NULLIF(v.view_count, 0)) AS avg_engagement_rate,

        AVG(v.duration_seconds)::numeric(18,2) AS avg_duration_seconds,

        SUM(CASE WHEN v.is_short THEN 1 ELSE 0 END) AS shorts_count,
        SUM(CASE WHEN NOT v.is_short THEN 1 ELSE 0 END) AS longform_count,

        SUM(CASE WHEN v.has_ad_keywords THEN 1 ELSE 0 END) AS ad_video_count,
        SUM(CASE WHEN v.has_external_links THEN 1 ELSE 0 END) AS linked_video_count,

        AVG(v.external_links_count)::numeric(18,2) AS avg_external_links_per_video,

        MIN(v.published_at) AS first_video_in_dataset,
        MAX(v.published_at) AS latest_video_in_dataset
    FROM videos v
    GROUP BY v.channel_id
)
SELECT
    c.channel_id,
    c.channel_title,
    c.country,
    c.published_at AS channel_created_at,

    c.subscriber_count,
    c.total_views,
    c.video_count,
    c.external_links_count AS channel_external_links_count,
    c.ecosystem_score,

    c.has_ad_keywords,
    c.has_affiliate_signals,
    c.has_marketplace_links,
    c.has_brand_store_links,
    c.has_instagram,
    c.has_telegram,
    c.has_tiktok,
    c.has_vk,
    c.has_twitter_x,
    c.has_facebook,
    c.has_discord,
    c.has_external_links,
    c.ecosystem_detected,

    vb.videos_in_dataset,
    vb.dataset_views,
    vb.avg_views_per_video,
    vb.median_views_per_video,
    vb.max_views,
    vb.min_views,

    ROUND(vb.avg_like_rate, 4) AS avg_like_rate,
    ROUND(vb.avg_comment_rate, 4) AS avg_comment_rate,
    ROUND(vb.avg_engagement_rate, 4) AS avg_engagement_rate,

    vb.avg_duration_seconds,
    vb.shorts_count,
    vb.longform_count,

    ROUND(vb.shorts_count::numeric / NULLIF(vb.videos_in_dataset, 0), 4) AS shorts_share,
    ROUND(vb.ad_video_count::numeric / NULLIF(vb.videos_in_dataset, 0), 4) AS ad_video_share,
    ROUND(vb.linked_video_count::numeric / NULLIF(vb.videos_in_dataset, 0), 4) AS linked_video_share,

    vb.avg_external_links_per_video,

    vb.first_video_in_dataset,
    vb.latest_video_in_dataset,

    -- publishing velocity based on dataset window
    ROUND(
        vb.videos_in_dataset::numeric /
        NULLIF(EXTRACT(DAY FROM (vb.latest_video_in_dataset - vb.first_video_in_dataset)), 0),
        4
    ) AS videos_per_day_in_dataset,

    -- normalized channel efficiency
    ROUND(vb.avg_views_per_video / NULLIF(c.subscriber_count, 0), 4) AS avg_views_per_video_per_subscriber

FROM channels c
LEFT JOIN video_base vb
    ON c.channel_id = vb.channel_id;


select * from channel_analytics;

-- Which channels overperform relative to subscribers?
SELECT
    channel_title,
    subscriber_count,
    avg_views_per_video,
    avg_views_per_video_per_subscriber,
    avg_engagement_rate
FROM channel_analytics
ORDER BY avg_views_per_video_per_subscriber DESC;

-- Do Shorts perform better than long-form?
SELECT
    is_short,
    COUNT(*) AS videos,
    AVG(view_count)::numeric(18,2) AS avg_views,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY view_count) AS median_views,
    AVG(engagement_rate)::numeric(18,4) AS avg_engagement_rate
FROM video_features
GROUP BY is_short
ORDER BY is_short DESC;


-- Are ad/sponsored videos weaker or stronger?
SELECT
    monetization_type,
    COUNT(*) AS videos,
    AVG(view_count)::numeric(18,2) AS avg_views,
    AVG(engagement_rate)::numeric(18,4) AS avg_engagement_rate,
    AVG(views_per_subscriber_count)::numeric(18,4) AS avg_views_per_subscriber
FROM video_features
GROUP BY monetization_type
ORDER BY avg_views DESC;

-- Best publishing days
SELECT
    publish_dow,
    COUNT(*) AS videos,
    AVG(view_count)::numeric(18,2) AS avg_views,
    AVG(engagement_rate)::numeric(18,4) AS avg_engagement_rate
FROM video_features
GROUP BY publish_dow
ORDER BY publish_dow;

-- Best publishing hours
SELECT
    publish_hour,
    COUNT(*) AS videos,
    AVG(view_count)::numeric(18,2) AS avg_views,
    AVG(engagement_rate)::numeric(18,4) AS avg_engagement_rate
FROM video_features
GROUP BY publish_hour
ORDER BY publish_hour;

-- Which channels rely most on monetization signals?
SELECT
    channel_title,
    videos_in_dataset,
    ad_video_share,
    linked_video_share,
    avg_external_links_per_video
FROM channel_analytics
ORDER BY ad_video_share DESC, linked_video_share DESC;

CREATE OR REPLACE VIEW video_performance_relative AS
WITH base AS (
    SELECT
        vf.*,
        AVG(view_count) OVER (PARTITION BY channel_id) AS channel_avg_views,
        AVG(engagement_rate) OVER (PARTITION BY channel_id) AS channel_avg_engagement
    FROM video_features vf
)
SELECT
    *,
    ROUND(view_count::numeric / NULLIF(channel_avg_views, 0), 4) AS view_index_vs_channel,
    ROUND(engagement_rate::numeric / NULLIF(channel_avg_engagement, 0), 4) AS engagement_index_vs_channel,
    CASE
        WHEN view_count::numeric / NULLIF(channel_avg_views, 0) >= 1.5 THEN 'outperformer'
        WHEN view_count::numeric / NULLIF(channel_avg_views, 0) < 0.75 THEN 'underperformer'
        ELSE 'normal'
    END AS performance_band
FROM base;

CREATE OR REPLACE VIEW video_cadence AS
SELECT
    v.channel_id,
    c.channel_title,
    v.video_id,
    v.published_at,
    LAG(v.published_at) OVER (PARTITION BY v.channel_id ORDER BY v.published_at) AS prev_video_published_at,
    EXTRACT(EPOCH FROM (
        v.published_at - LAG(v.published_at) OVER (PARTITION BY v.channel_id ORDER BY v.published_at)
    )) / 86400 AS days_since_previous_video
FROM videos v
LEFT JOIN channels c
    ON v.channel_id = c.channel_id;

CREATE OR REPLACE VIEW video_features_enhanced AS
SELECT
    vf.*,
    LN(vf.view_count + 1) AS log_views,
    LN(vf.like_count + 1) AS log_likes,
    LN(vf.comment_count + 1) AS log_comments
FROM video_features vf;

select * from channel_analytics;
select * from video_cadence;
select * from video_features;
select * from video_features_enhanced;
select * from video_performance_relative;
