import feedparser
import datetime


def fetch_feed(feed_url, max_articles=5):
    """Fetch articles from an RSS feed. Returns list of dicts."""
    try:
        parsed = feedparser.parse(feed_url)
        articles = []
        for entry in parsed.entries[:max_articles]:
            title = entry.get('title', '').strip()
            summary = entry.get('summary', entry.get('description', '')).strip()
            # Strip HTML tags from summary
            import re
            summary = re.sub(r'<[^>]+>', '', summary).strip()
            summary = summary[:300] if summary else ''
            link = entry.get('link', '')
            articles.append({
                'title': title,
                'summary': summary,
                'link': link,
            })
        return articles, parsed.feed.get('title', feed_url)
    except Exception as e:
        raise RuntimeError(f"Could not fetch feed '{feed_url}': {e}")


def fetch_all_feeds(feeds, max_per_feed=5):
    """Fetch all configured feeds. Returns list of (feed_name, articles) tuples."""
    results = []
    errors = []
    for feed in feeds:
        try:
            articles, feed_title = fetch_feed(feed['url'], max_per_feed)
            name = feed.get('name') or feed_title
            if articles:
                results.append((name, articles))
        except Exception as e:
            errors.append(str(e))
    return results, errors
