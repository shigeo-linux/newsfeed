#!/usr/bin/env python3
import sys
import os
import datetime
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config, LOG_FILE, CONFIG_DIR
from feed_client import fetch_all_feeds
from summarizer import summarize_feeds
from telegram_client import send_message, TelegramError

os.makedirs(CONFIG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)


def run():
    config = Config()
    now = datetime.datetime.now()
    now_str = now.isoformat(sep=' ', timespec='seconds')
    today = now.strftime('%Y-%m-%d')

    if not config.feeds:
        logging.error("No feeds configured.")
        config.set('last_status', 'Error: No feeds configured')
        config.save()
        sys.exit(1)

    # Determine if we should send morning or evening edition
    edition = None
    if now.hour == config.morning_hour and config.get('last_morning_sent') != today:
        edition = 'Morning'
        sent_key = 'last_morning_sent'
    elif config.evening_hour >= 0 and now.hour == config.evening_hour and config.get('last_evening_sent') != today:
        edition = 'Evening'
        sent_key = 'last_evening_sent'

    if not edition:
        config.set('last_run', now_str)
        config.set('last_status', f'OK — checked at {now.strftime("%H:%M")}, not send time')
        config.save()
        return

    try:
        logging.info(f"Fetching {len(config.feeds)} feeds for {edition} edition")
        feed_results, errors = fetch_all_feeds(config.feeds, config.max_articles_per_feed)

        if errors:
            for e in errors:
                logging.warning(f"Feed error: {e}")

        logging.info(f"Fetched {len(feed_results)} feeds, summarising")
        summary = summarize_feeds(feed_results, config, edition=edition)
        send_message(config.telegram_token, config.telegram_chat_id, summary)

        config.set(sent_key, today)
        config.set('last_run', now_str)
        config.set('last_status', f'OK — {edition} briefing sent ({len(feed_results)} feeds)')
        config.save()
        logging.info(f"{edition} briefing sent successfully")

    except TelegramError as e:
        msg = f'Telegram error: {str(e)[:120]}'
        logging.error(msg)
        config.set('last_run', now_str)
        config.set('last_status', f'Error: {msg}')
        config.save()
        sys.exit(1)

    except Exception as e:
        msg = str(e)[:120]
        logging.error(f"Error: {msg}")
        config.set('last_run', now_str)
        config.set('last_status', f'Error: {msg}')
        config.save()
        sys.exit(1)


if __name__ == '__main__':
    run()
