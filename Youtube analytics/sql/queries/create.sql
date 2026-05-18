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

create or replace view channel_analytics as
with video_base as (
	select
		v.channel_id,
		count(*) as videos_in_datase
)