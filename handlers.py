"""
The handler module includes the following elements:

- The definition of a Scraper class, that models a worker searching
for updates every T seconds.

- A series of handlers that are wrapped with a dictionary containing
the urls that are being monitored, and are given as input to the
telegram bot CommandHandlers.
"""

from typing import Optional, Callable, Any

import threading
import functools
import requests

from telegram.ext import CallbackContext
from telegram import Update, Bot


class Scraper:
    """
    Scraper defines a class that can monitor an URL and check for differences in the contents
    of the GET request reply.

    By default, the interval at which a Scraper object updates itself is 15 minutes.
    Try not to pass an interval that is too small, in order not to overload the server you are
    connecting to.
    """
    def __init__(self, chat_id: str, bot: Bot, endp: str, interval: Optional[int] = None) -> None:
        self._evt = threading.Event()
        self._endp = endp
        self._chat_id = chat_id
        self._thread = threading.Thread(target=self._search_for_updates, args=(bot,))

        if interval is not None and interval <= 0:
            raise ValueError("Interval must be positive")
        self._interval = 15 * 60 if interval is None else interval

    @property
    def endpoint(self) -> str:
        """
        The endpoint that is being monitored by this Scraper.
        :return: str, the endpoint URL
        """
        return self._endp

    @property
    def timer(self) -> int:
        """
        The time interval at which this Scraper operates.
        :return: int, the interval
        """
        return self._interval

    @timer.setter
    def timer(self, interval: int) -> None:
        """
        Set a new interval for the Scraper object.
        This will reset the scraper activity.
        :param interval: int, the new interval
        :return: None
        """
        self._interval = interval
        self.stop()

        self._evt = threading.Event()
        self.start()

    def start(self) -> None:
        """
        Starts the monitoring activity for this Scraper.
        :return: None
        """
        self._thread.start()

    def stop(self) -> None:
        """
        Stops the monitoring activity for this Scraper.
        :return: None
        """
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
"""UrlDict represents the url dict type."""

RCallback = Callable[[UrlDict, Update, CallbackContext], Any]
"""RCallback represents the augmented callback type that includes the url dict object."""


def help_cmds(update: Update, _: CallbackContext) -> None:
    """
    Handler that returns the help/usage message to the user.
    :param update: the telegram Update object
    :param _: the telegram CallbackContext object
    :return: None
    """
    help_msg = r"""update_notifier: monitor urls and receive updates via telegram
/help -> show this message
/add [name] [url] [interval]-> start monitoring for the passed url identified by name, interval default is 15 mins
/remove [name] -> remove an url under monitoring, identified by its name
/list -> list all the urls under monitoring
/timer [name] -> return the current interval for the url identified by name
/set_timer [name] [interval] -> reset the monitor for the url with the new interval
/end -> stop monitoring every url
"""
    update.message.reply_text(help_msg)


def add(urls: UrlDict, update: Update, context: CallbackContext) -> None:
    """
    Add a new URL to monitor to the system.
    :param urls: a reference to the users/url dict
    :param update: the telegram Update object
    :param context: the telegram CallbackContext object
    :return: None
    """
    try:
        name = context.args[0]
        url = context.args[1]
        chat_id = update.effective_chat.id
        if chat_id not in urls:
            urls[chat_id] = {}

        if len(context.args) == 3:
            interval = int(context.args[2])
            urls[chat_id][name] = Scraper(chat_id, update.effective_chat.bot, url, interval)
        else:
            urls[chat_id][name] = Scraper(chat_id, update.effective_chat.bot, url)

        urls[chat_id][name].start()
        update.message.reply_text(f"monitoring: {name}")
    except IndexError:
        update.message.reply_text("you have to pass a name and a url to add")
    except ValueError:
        update.message.reply_text("interval must be a positive integer")


def remove(urls: UrlDict, update: Update, context: CallbackContext) -> None:
    """
    Removes a URL from the monitor, if it exists.
    :param urls: a reference to the users/url dict
    :param update: the telegram Update object
    :param context: the telegram CallbackContext object
    :return: None
    """
    try:
        name = context.args[0]
        chat_id = update.effective_chat.id
        if name in urls[chat_id]:
            scraper = urls[chat_id].pop(name)
            scraper.stop()
            update.message.reply_text(f"stopping the monitor for: {name}")
            return
        update.message.reply_text(f"no active monitor for: {name}")
    except IndexError:
        update.message.reply_text("you have to pass the name of an url to remove")


def list_urls(urls: UrlDict, update: Update, _: CallbackContext) -> None:
    """
    Lists all the URL names that are currently being monitored for the user.
    :param urls: a reference to the users/url dict
    :param update: the telegram Update object
    :param _: the telegram CallbackContext object
    :return: None
    """
    chat_id = update.effective_chat.id
    if chat_id not in urls or len(urls[chat_id]) == 0:
        urls[chat_id] = {}
        update.message.reply_text("no urls are being monitored")
        return
    update.message.reply_text("\n".join(urls[chat_id].keys()))


def end(urls: UrlDict, update: Update, _: CallbackContext) -> None:
    """
    Removes all the monitored URLs that are being monitored for the user.
    :param urls: a reference to the users/url dict
    :param update: the telegram Update object
    :param _: the telegram CallbackContext object
    :return: None
    """
    if update.effective_chat.id in urls:
        user = urls.pop(update.effective_chat.id)
        for name, scraper in user.items():
            scraper.stop()
            update.message.reply_text(f"stopping the monitor for: {name}")
    update.message.reply_text("stopping the monitor task for your user")


def timer(urls: UrlDict, update: Update, context: CallbackContext) -> None:
    """
    Returns the interval used by the scraper for the specific URL.
    :param urls: a reference to the users/url dict
    :param update: the telegram Update object
    :param context: the telegram CallbackContext object
    :return: None
    """
    try:
        name = context.args[0]
        chat_id = update.effective_chat.id
        update.message.reply_text(f"current timer for {name}: {urls[chat_id][name].timer}s")
    except IndexError:
        update.message.reply_text("you have to pass the name of an url")
    except KeyError:
        update.message.reply_text("no such url under monitoring")


def timer_set(urls: UrlDict, update: Update, context: CallbackContext) -> None:
    """
    Sets the interval used by the scraper for the specific URL.
    :param urls: a reference to the users/url dict
    :param update: the telegram Update object
    :param context: the telegram CallbackContext object
    :return: None
    """
    try:
        name = context.args[0]
        interval = int(context.args[1])
        chat_id = update.effective_chat.id
        if interval <= 0:
            update.message.reply_text("interval must be a positive integer")
            return
        urls[chat_id][name].timer = interval
        update.message.reply_text(f"new timer for {name}: {urls[chat_id][name].timer}s")
    except IndexError:
        update.message.reply_text("you have to pass the name of an url and a positive interval")
    except ValueError:
        update.message.reply_text("interval must be a positive integer")
    except KeyError:
        update.message.reply_text("no such url under monitoring")


def wrap_handler(handler: RCallback, urls: UrlDict) -> Callable[[Update, Any], Any]:
    """
    Wraps an RCallback so to return a callback that is compatible with
    the python-telegram-bot library.
    :param handler: the RCallback handler
    :param urls: the url dict object
    :return: a callback with the url dict as internal state
    """
    return functools.partial(handler, urls)
