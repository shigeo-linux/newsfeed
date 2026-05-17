# Newsfeed

An AI-powered news digest for Linux that sends a summary of top headlines from your chosen RSS feeds to Telegram. Get a morning briefing, an optional evening briefing, or trigger one on demand.

---

## Features

- **Morning and evening briefings** — sent automatically at your chosen times
- **Fully configurable RSS feeds** — add or remove any RSS feed in the app
- **AI summarisation** — headlines from all feeds combined into a clean briefing
- **Runs automatically** — systemd timer checks every hour in the background
- **Send Now button** — trigger a briefing at any time to test or catch up
- **GTK settings window** — manage feeds, schedule, Telegram, and AI model

---

## Requirements

- Ubuntu 24.04 / Linux Mint 22.x (or any systemd-based Linux)
- Python 3.10+
- An OpenRouter API key (free tier at [openrouter.ai/keys](https://openrouter.ai/keys))
- A Telegram bot token and chat ID

---

## Installation

```bash
cd newsfeed/
chmod +x install.sh
./install.sh
```

Then launch:
```bash
newsfeed
```

---

## Setup

1. Launch Newsfeed
2. Enter your **Telegram bot token** and **chat ID**
3. Enter your **OpenRouter API key**
4. Set your **morning briefing hour** (24h format) and optional **evening hour** (-1 to disable)
5. Add or remove RSS feeds as desired
6. Click **Save Settings**
7. Click **Send Briefing Now** to test

---

## Default RSS feeds

| Source | URL |
|---|---|
| BBC News | `http://feeds.bbci.co.uk/news/rss.xml` |
| NPR News | `https://feeds.npr.org/1001/rss.xml` |
| The Guardian | `https://www.theguardian.com/world/rss` |

### Other feeds known to work

| Source | URL |
|---|---|
| CNN | `http://rss.cnn.com/rss/edition.rss` |
| ABC News | `https://abcnews.go.com/abcnews/topstories` |
| NY Times World | `https://rss.nytimes.com/services/xml/rss/nyt/World.xml` |
| Al Jazeera | `https://www.aljazeera.com/xml/rss/all.xml` |
| Washington Post | `https://feeds.washingtonpost.com/rss/world` |

---

## Example Telegram message

```
📰 News Briefing

BBC News
• Ukraine peace talks stall — Negotiations have broken down over territory disputes ahead of a key summit.
• UK interest rates held — The Bank of England kept rates at 4.5% citing ongoing inflation concerns.

NPR News
• US Senate passes budget bill — A last-minute deal averted a government shutdown through September.

The Guardian
• Amazon deforestation drops — Brazil reports a 40% reduction in deforestation in the first quarter.

🕐 Newsfeed Morning briefing — 07:00 on 17 May 2026
```

---

## Managing the timer

```bash
systemctl --user status newsfeed.timer
systemctl --user stop newsfeed.timer
systemctl --user disable newsfeed.timer
```

---

## Data storage

| Data | Location |
|---|---|
| Settings & feeds | `~/.config/newsfeed/config.json` |
| Activity log | `~/.config/newsfeed/newsfeed.log` |

---

## Uninstall

```bash
systemctl --user stop newsfeed.timer
systemctl --user disable newsfeed.timer
rm ~/.config/systemd/user/newsfeed.*
sudo rm -rf /opt/newsfeed
sudo rm -f /usr/local/bin/newsfeed
sudo rm -f /usr/share/applications/newsfeed.desktop
sudo rm -f /usr/share/icons/hicolor/scalable/apps/newsfeed.svg
rm -rf ~/.config/newsfeed
```
