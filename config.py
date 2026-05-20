import json
import os

CONFIG_DIR = os.path.expanduser('~/.config/newsfeed')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
LOG_FILE = os.path.join(CONFIG_DIR, 'newsfeed.log')

DEFAULT_FEEDS = [
    {'name': 'BBC News',      'url': 'http://feeds.bbci.co.uk/news/rss.xml'},
    {'name': 'NPR News',      'url': 'https://feeds.npr.org/1001/rss.xml'},
    {'name': 'The Guardian',  'url': 'https://www.theguardian.com/world/rss'},
]

DEFAULTS = {
    'api_key': '',
    'model': 'openrouter/auto',
    'base_url': 'https://openrouter.ai/api/v1',
    'telegram_token': '',
    'telegram_chat_id': '',
    'feeds': DEFAULT_FEEDS,
    'morning_hour': 7,
    'evening_hour': -1,  # -1 = disabled
    'max_articles_per_feed': 5,
    'last_morning_sent': '',
    'last_evening_sent': '',
    'last_run': '',
    'last_status': '',
}


class Config:
    def __init__(self):
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self._data.update(json.load(f))
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self._data, f, indent=2)

    def get(self, key, fallback=None):
        return self._data.get(key, fallback if fallback is not None else DEFAULTS.get(key))

    def set(self, key, value):
        self._data[key] = value

    @property
    def api_key(self):
        return self._data.get('api_key', '')

    @api_key.setter
    def api_key(self, value):
        self._data['api_key'] = value

    @property
    def model(self):
        return self._data.get('model', DEFAULTS['model'])

    @model.setter
    def model(self, value):
        self._data['model'] = value

    @property
    def base_url(self):
        return self._data.get('base_url', DEFAULTS['base_url'])

    @property
    def telegram_token(self):
        return self._data.get('telegram_token', '')

    @property
    def telegram_chat_id(self):
        return self._data.get('telegram_chat_id', '')

    @property
    def feeds(self):
        return self._data.get('feeds', DEFAULT_FEEDS)

    @property
    def morning_hour(self):
        return int(self._data.get('morning_hour', 7))

    @property
    def evening_hour(self):
        return int(self._data.get('evening_hour', -1))

    @property
    def max_articles_per_feed(self):
        return int(self._data.get('max_articles_per_feed', 5))
