import os
import subprocess
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from config import Config, LOG_FILE
from api_client import APIClient
from feed_client import fetch_all_feeds
from summarizer import summarize_feeds
from telegram_client import send_message, test_connection, TelegramError

STYLE_PATH = os.path.join(os.path.dirname(__file__), 'style.css')

MODELS = [
    'openrouter/auto',
    'anthropic/claude-3.5-sonnet',
    'anthropic/claude-3-opus',
    'openai/gpt-4o',
    'openai/gpt-4o-mini',
    'google/gemini-pro-1.5',
]


def _load_css():
    provider = Gtk.CssProvider()
    try:
        provider.load_from_path(STYLE_PATH)
    except Exception:
        pass
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


def fl(text):
    lbl = Gtk.Label(label=text, xalign=1)
    lbl.get_style_context().add_class('field-label')
    return lbl


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title='Newsfeed')
        self.set_default_size(580, 680)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name('newsfeed')
        _load_css()

        self.config = Config()
        self._busy = False
        self._build_ui()
        self._refresh_status()

    def _build_ui(self):
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title('Newsfeed')
        header.set_subtitle('News digests → Telegram')
        self.set_titlebar(header)

        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_border_width(20)
        scroll.add(content)
        main.pack_start(scroll, True, True, 0)

        # ── Status ────────────────────────────────────────────────
        status_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        status_card.get_style_context().add_class('status-card')

        lbl = Gtk.Label(label='Status', xalign=0)
        lbl.get_style_context().add_class('section-title')
        status_card.pack_start(lbl, False, False, 0)

        self._status_label = Gtk.Label(label='Not yet run', xalign=0)
        self._status_label.set_line_wrap(True)
        self._status_label.set_max_width_chars(60)
        self._status_label.get_style_context().add_class('status-pending')
        status_card.pack_start(self._status_label, False, False, 0)

        self._last_run_label = Gtk.Label(label='', xalign=0)
        self._last_run_label.set_ellipsize(3)
        self._last_run_label.set_max_width_chars(60)
        self._last_run_label.get_style_context().add_class('meta-label')
        status_card.pack_start(self._last_run_label, False, False, 0)
        content.pack_start(status_card, False, False, 0)

        # ── Run now ───────────────────────────────────────────────
        run_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self._run_btn = Gtk.Button(label='Send Briefing Now')
        self._run_btn.get_style_context().add_class('action-btn')
        self._run_btn.connect('clicked', self._on_run_now)
        run_row.pack_start(self._run_btn, False, False, 0)
        self._spinner = Gtk.Spinner()
        run_row.pack_start(self._spinner, False, False, 0)
        content.pack_start(run_row, False, False, 0)

        content.pack_start(Gtk.Separator(), False, False, 0)

        # ── Telegram ──────────────────────────────────────────────
        tg_title = Gtk.Label(label='Telegram', xalign=0)
        tg_title.get_style_context().add_class('section-title')
        content.pack_start(tg_title, False, False, 0)

        tg_grid = Gtk.Grid()
        tg_grid.set_column_spacing(12)
        tg_grid.set_row_spacing(8)

        tg_grid.attach(fl('Token:'), 0, 0, 1, 1)
        self._tg_token_entry = Gtk.Entry()
        self._tg_token_entry.set_hexpand(True)
        self._tg_token_entry.set_visibility(False)
        self._tg_token_entry.set_text(self.config.telegram_token)
        self._tg_token_entry.set_placeholder_text('123456789:ABCdef...')
        tg_grid.attach(self._tg_token_entry, 1, 0, 1, 1)

        tg_grid.attach(fl('Chat ID:'), 0, 1, 1, 1)
        self._tg_chat_entry = Gtk.Entry()
        self._tg_chat_entry.set_text(self.config.telegram_chat_id)
        tg_grid.attach(self._tg_chat_entry, 1, 1, 1, 1)
        content.pack_start(tg_grid, False, False, 0)

        content.pack_start(Gtk.Separator(), False, False, 0)

        # ── Schedule ──────────────────────────────────────────────
        sch_title = Gtk.Label(label='Schedule', xalign=0)
        sch_title.get_style_context().add_class('section-title')
        content.pack_start(sch_title, False, False, 0)

        sch_grid = Gtk.Grid()
        sch_grid.set_column_spacing(12)
        sch_grid.set_row_spacing(8)

        sch_grid.attach(fl('Morning briefing:'), 0, 0, 1, 1)
        morning_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._morning_spin = Gtk.SpinButton.new_with_range(0, 23, 1)
        self._morning_spin.set_value(self.config.morning_hour)
        self._morning_spin.set_size_request(60, -1)
        morning_box.pack_start(self._morning_spin, False, False, 0)
        lbl2 = Gtk.Label(label=':00  (24h)')
        lbl2.get_style_context().add_class('field-label')
        morning_box.pack_start(lbl2, False, False, 0)
        sch_grid.attach(morning_box, 1, 0, 1, 1)

        sch_grid.attach(fl('Evening briefing:'), 0, 1, 1, 1)
        eve_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._evening_spin = Gtk.SpinButton.new_with_range(-1, 23, 1)
        self._evening_spin.set_value(self.config.evening_hour)
        self._evening_spin.set_size_request(60, -1)
        eve_box.pack_start(self._evening_spin, False, False, 0)
        lbl3 = Gtk.Label(label=':00  (-1 = disabled)')
        lbl3.get_style_context().add_class('field-label')
        eve_box.pack_start(lbl3, False, False, 0)
        sch_grid.attach(eve_box, 1, 1, 1, 1)

        sch_grid.attach(fl('Articles per feed:'), 0, 2, 1, 1)
        self._max_spin = Gtk.SpinButton.new_with_range(1, 10, 1)
        self._max_spin.set_value(self.config.max_articles_per_feed)
        sch_grid.attach(self._max_spin, 1, 2, 1, 1)
        content.pack_start(sch_grid, False, False, 0)

        content.pack_start(Gtk.Separator(), False, False, 0)

        # ── AI model ──────────────────────────────────────────────
        ai_title = Gtk.Label(label='AI Model (OpenRouter)', xalign=0)
        ai_title.get_style_context().add_class('section-title')
        content.pack_start(ai_title, False, False, 0)

        ai_grid = Gtk.Grid()
        ai_grid.set_column_spacing(12)
        ai_grid.set_row_spacing(8)

        ai_grid.attach(fl('API Key:'), 0, 0, 1, 1)
        self._api_key_entry = Gtk.Entry()
        self._api_key_entry.set_hexpand(True)
        self._api_key_entry.set_visibility(False)
        self._api_key_entry.set_text(self.config.api_key)
        self._api_key_entry.set_placeholder_text('sk-or-...')
        ai_grid.attach(self._api_key_entry, 1, 0, 1, 1)

        ai_grid.attach(fl('Model:'), 0, 1, 1, 1)
        self._model_combo = Gtk.ComboBoxText()
        for m in MODELS:
            self._model_combo.append(m, m)
        self._model_combo.set_active_id(
            self.config.model if self.config.model in MODELS else MODELS[0]
        )
        ai_grid.attach(self._model_combo, 1, 1, 1, 1)
        content.pack_start(ai_grid, False, False, 0)

        content.pack_start(Gtk.Separator(), False, False, 0)

        # ── Feeds ─────────────────────────────────────────────────
        feeds_title = Gtk.Label(label='RSS Feeds', xalign=0)
        feeds_title.get_style_context().add_class('section-title')
        content.pack_start(feeds_title, False, False, 0)

        # Feed list
        feed_scroll = Gtk.ScrolledWindow()
        feed_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        feed_scroll.set_min_content_height(120)
        feed_scroll.set_max_content_height(160)

        self._feed_list = Gtk.ListBox()
        self._feed_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._feed_list.get_style_context().add_class('feed-row')
        feed_scroll.add(self._feed_list)
        content.pack_start(feed_scroll, False, False, 0)
        self._refresh_feed_list()

        # Add feed row
        add_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._feed_name_entry = Gtk.Entry()
        self._feed_name_entry.set_placeholder_text('Feed name (e.g. BBC News)')
        self._feed_name_entry.set_hexpand(True)
        add_row.pack_start(self._feed_name_entry, True, True, 0)

        self._feed_url_entry = Gtk.Entry()
        self._feed_url_entry.set_placeholder_text('RSS URL')
        self._feed_url_entry.set_hexpand(True)
        self._feed_url_entry.connect('activate', self._on_add_feed)
        add_row.pack_start(self._feed_url_entry, True, True, 0)

        add_btn = Gtk.Button(label='Add')
        add_btn.get_style_context().add_class('action-btn')
        add_btn.connect('clicked', self._on_add_feed)
        add_row.pack_start(add_btn, False, False, 0)

        rem_btn = Gtk.Button(label='Remove')
        rem_btn.get_style_context().add_class('danger-btn')
        rem_btn.connect('clicked', self._on_remove_feed)
        add_row.pack_start(rem_btn, False, False, 0)
        content.pack_start(add_row, False, False, 0)

        # ── Buttons ───────────────────────────────────────────────
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        save_btn = Gtk.Button(label='Save Settings')
        save_btn.get_style_context().add_class('action-btn')
        save_btn.connect('clicked', self._on_save)
        btn_row.pack_start(save_btn, False, False, 0)

        test_btn = Gtk.Button(label='Test Telegram')
        test_btn.connect('clicked', self._on_test_telegram)
        btn_row.pack_start(test_btn, False, False, 0)

        log_btn = Gtk.Button(label='View Log')
        log_btn.connect('clicked', self._on_view_log)
        btn_row.pack_end(log_btn, False, False, 0)
        content.pack_start(btn_row, False, False, 0)

        # Status bar
        self._status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._status_bar.get_style_context().add_class('status-bar')
        self._bar_label = Gtk.Label(label='', xalign=0)
        self._status_bar.pack_start(self._bar_label, True, True, 0)
        main.pack_start(self._status_bar, False, False, 0)

    def _refresh_feed_list(self):
        for child in self._feed_list.get_children():
            self._feed_list.remove(child)
        for feed in self.config.feeds:
            row = Gtk.ListBoxRow()
            row.get_style_context().add_class('feed-row')
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            box.set_border_width(4)
            name_lbl = Gtk.Label(label=feed.get('name', ''), xalign=0)
            name_lbl.get_style_context().add_class('field-label')
            name_lbl.set_size_request(150, -1)
            box.pack_start(name_lbl, False, False, 0)
            url_lbl = Gtk.Label(label=feed.get('url', ''), xalign=0)
            url_lbl.get_style_context().add_class('meta-label')
            url_lbl.set_ellipsize(3)
            box.pack_start(url_lbl, True, True, 0)
            row.add(box)
            self._feed_list.add(row)
        self._feed_list.show_all()

    def _on_add_feed(self, widget):
        name = self._feed_name_entry.get_text().strip()
        url = self._feed_url_entry.get_text().strip()
        if not url:
            return
        feeds = list(self.config.feeds)
        feeds.append({'name': name or url, 'url': url})
        self.config.set('feeds', feeds)
        self.config.save()
        self._feed_name_entry.set_text('')
        self._feed_url_entry.set_text('')
        self._refresh_feed_list()
        self._set_bar(f'Feed added: {name or url}')

    def _on_remove_feed(self, widget):
        row = self._feed_list.get_selected_row()
        if row is None:
            self._set_bar('Select a feed to remove.')
            return
        idx = row.get_index()
        feeds = list(self.config.feeds)
        if 0 <= idx < len(feeds):
            removed = feeds.pop(idx)
            self.config.set('feeds', feeds)
            self.config.save()
            self._refresh_feed_list()
            self._set_bar(f'Removed: {removed.get("name", "")}')

    def _refresh_status(self):
        last_run = self.config.get('last_run', '')
        last_status = self.config.get('last_status', '')
        ctx = self._status_label.get_style_context()
        if last_status.startswith('OK'):
            self._status_label.set_text(last_status)
            ctx.add_class('status-ok')
            ctx.remove_class('status-error')
            ctx.remove_class('status-pending')
        elif last_status.startswith('Error'):
            self._status_label.set_text(last_status[:120])
            ctx.add_class('status-error')
            ctx.remove_class('status-ok')
            ctx.remove_class('status-pending')
        else:
            self._status_label.set_text('Not yet run')
        self._last_run_label.set_text(f'Last run: {last_run}' if last_run else 'Last run: never')

    def _on_save(self, btn):
        self.config.set('telegram_token', self._tg_token_entry.get_text().strip())
        self.config.set('telegram_chat_id', self._tg_chat_entry.get_text().strip())
        self.config.set('morning_hour', int(self._morning_spin.get_value()))
        self.config.set('evening_hour', int(self._evening_spin.get_value()))
        self.config.set('max_articles_per_feed', int(self._max_spin.get_value()))
        self.config.api_key = self._api_key_entry.get_text().strip()
        self.config.model = self._model_combo.get_active_id()
        self.config.save()
        self._set_bar('Settings saved.')

    def _on_test_telegram(self, btn):
        token = self._tg_token_entry.get_text().strip()
        chat_id = self._tg_chat_entry.get_text().strip()
        if not token or not chat_id:
            self._show_error('Missing details', 'Enter your Telegram token and chat ID first.')
            return
        try:
            test_connection(token, chat_id)
            self._set_bar('Test message sent to Telegram.')
        except TelegramError as e:
            self._show_error('Telegram test failed', str(e))

    def _on_run_now(self, btn):
        if self._busy:
            return
        if not self.config.feeds:
            self._show_error('No feeds', 'Add at least one RSS feed first.')
            return
        self._busy = True
        self._run_btn.set_sensitive(False)
        self._spinner.start()

        def run():
            try:
                feed_results, errors = fetch_all_feeds(
                    self.config.feeds, self.config.max_articles_per_feed
                )
                summary = summarize_feeds(feed_results, self.config, edition='Briefing')
                send_message(self.config.telegram_token, self.config.telegram_chat_id, summary)
                GLib.idle_add(self._on_run_done, True, f'Briefing sent ({len(feed_results)} feeds).')
            except Exception as e:
                GLib.idle_add(self._on_run_done, False, str(e)[:120])

        threading.Thread(target=run, daemon=True).start()

    def _on_run_done(self, success, msg):
        self._busy = False
        self._spinner.stop()
        self._run_btn.set_sensitive(True)
        self._set_bar(msg)

    def _on_view_log(self, btn):
        if os.path.exists(LOG_FILE):
            subprocess.Popen(['xdg-open', LOG_FILE])
        else:
            self._set_bar('No log file yet.')

    def _set_bar(self, msg):
        self._bar_label.set_text(msg)

    def _show_error(self, title, msg):
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK, text=title,
        )
        dialog.format_secondary_text(msg)
        dialog.run()
        dialog.destroy()
