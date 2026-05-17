import datetime
from api_client import APIClient, APIError

SUMMARY_SYSTEM = """You are a news editor. You will be given headlines and summaries from several news feeds. Produce a concise news briefing for Telegram.

Format your response exactly like this:

📰 <b>News Briefing</b>

For each feed, one section:
<b>[Feed Name]</b>
• [Headline] — [one sentence summary]
• [Headline] — [one sentence summary]

Keep bullet points tight and informative. Skip duplicates across feeds. Focus on the most important and interesting stories. Use plain language. No more than 3 bullets per feed."""


def build_feed_text(feed_results):
    parts = []
    for name, articles in feed_results:
        feed_lines = [f"Feed: {name}"]
        for a in articles:
            line = f"- {a['title']}"
            if a['summary']:
                line += f": {a['summary'][:200]}"
            feed_lines.append(line)
        parts.append('\n'.join(feed_lines))
    return '\n\n'.join(parts)


def summarize_feeds(feed_results, config, edition='Morning'):
    if not feed_results:
        now = datetime.datetime.now().strftime('%H:%M on %-d %b %Y')
        return f"📰 <b>Newsfeed</b> — No articles fetched.\n🕐 {now}"

    api = APIClient(config)
    feed_text = build_feed_text(feed_results)

    summary = api.complete(
        messages=[{'role': 'user', 'content': f"Here are today's news articles:\n\n{feed_text}"}],
        system=SUMMARY_SYSTEM,
    )

    now = datetime.datetime.now().strftime('%H:%M on %-d %b %Y')
    return f"{summary}\n\n🕐 <i>Newsfeed {edition} briefing — {now}</i>"
