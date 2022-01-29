from typing import Optional, Callable, Any
from telegram.ext import CallbackContext
from telegram import Update, Bot

import threading
import functools
import requests


class Scraper:
    def __init__(self, chat_id: str, bot: Bot, endp: str, interval: Optional[int] = None):
        self._evt = threading.Event()
        self._endp = endp
        self._chat_id = chat_id
        self._thread = threading.Thread(target=self._search_for_updates, args=(bot,))

        if interval is not None and interval <= 0:
            raise ValueError("Interval must be positive")
        self._interval = 15 * 60 if interval is None else interval

    @property
    def endpoint(self) -> str:
        return self._endp

    @property
    def timer(self) -> int:
        return self._interval

    @timer.setter
    def timer(self, interval: int) -> None:
        self._interval = interval
        self.stop()

        self._evt = threading.Event()
        self.start()

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._evt.set()

    def _search_for_updates(self, bot: Bot) -> None:
        cache = requests.get(self._endp).text
        while not self._evt.wait(self._interval):
            try:
                body = requests.get(self._endp).text
            except:
                bot.send_message("invalid endpoint, closing connection...")
                return

            if body != cache:
                bot.send_message(chat_id=self._chat_id, text=f"Updated: {self._endp}")
                cache = body


UrlDict = dict[str, dict[str, Scraper]]
RCallback = Callable[[UrlDict, Update, CallbackContext], Any]


def help_cmds(update: Update, context: CallbackContext) -> None:
    help_msg = r"""/help -> show this message
    /add [name] [url] [interval]-> start monitoring for the passed url identified by name, interval default is 15 mins
    /remove [name] -> remove an url under monitoring, identified by its name
    /list -> list all the urls under monitoring
    /timer [name] -> return the current interval for the url identified by name
    /set_timer [name] [interval] -> reset the monitor for the url with the new interval
    /end -> stop monitoring every url
    """
    update.message.reply_text(help_msg)


def add(urls: UrlDict, update: Update, context: CallbackContext) -> None:
    try:
        name = context.args[0]
        url = context.args[1]
        chat_id = update.effective_chat.id
        if chat_id not in urls:
            urls[chat_id] = {}

        if len(context.args) == 3:
            urls[chat_id][name] = Scraper(chat_id, update.effective_chat.bot, url, int(context.args[2]))
        else:
            urls[chat_id][name] = Scraper(chat_id, update.effective_chat.bot, url)

        update.message.reply_text(f"monitoring: {name}")
    except IndexError:
        update.message.reply_text("you have to pass a name and a url to add")
    except ValueError:
        update.message.reply_text("interval must be a positive integer")


def remove(urls: UrlDict, update: Update, context: CallbackContext) -> None:
    try:
        name = context.args[0]
        chat_id = update.effective_chat.id
        if name in urls[chat_id]:
            scraper = urls[chat_id].pop(name)
            scraper.stop()
            update.message.reply_text(f"stopping the monitor for: {name}")
    except IndexError:
        update.message.reply_text("you have to pass the name of an url to remove")


def list_urls(urls: UrlDict, update: Update, _: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    update.message.reply_text("\n".join(urls[chat_id].keys()))


def end(urls: UrlDict, update: Update, _: CallbackContext) -> None:
    if update.effective_chat.id in urls:
        user = urls.pop(update.effective_chat.id)
        for name, scraper in user:
            scraper.stop()
            update.message.reply_text(f"stopping the monitor for: {name}")
    update.message.reply_text("stopping the monitor task for your user")


def timer(urls: UrlDict, update: Update, context: CallbackContext) -> None:
    try:
        name = context.args[0]
        chat_id = update.effective_chat.id
        update.message.reply_text(f"current timer for {name}: {urls[chat_id][name].timer}")
    except IndexError:
        update.message.reply_text("you have to pass the name of an url")
    except KeyError:
        update.message.reply_text("no such url under monitoring")


def timer_set(urls: UrlDict, update: Update, context: CallbackContext) -> None:
    try:
        name = context.args[0]
        interval = int(context.args[1])
        chat_id = update.effective_chat.id
        if interval <= 0:
            update.message.reply_text(f"interval must be a positive integer")
            return
        urls[chat_id][name].timer = interval
        update.message.reply_text(f"new timer for {name}: {urls[chat_id][name].timer}")
    except IndexError:
        update.message.reply_text("you have to pass the name of an url and a positive interval")
    except ValueError:
        update.message.reply_text(f"interval must be a positive integer")
    except KeyError:
        update.message.reply_text("no such url under monitoring")


def wrap_handler(handler: RCallback, urls: UrlDict) -> Callable[[Update, Any], Any]:
    return functools.partial(handler, urls=urls)
