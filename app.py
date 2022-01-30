"""
Powered by Antima.it, Gianmarco Marcello
Main entrypoint for the update_notifier application.
"""

import sys
import os

from telegram.ext import Updater, CommandHandler
from handlers import wrap_handler, help_cmds, add, remove, list_urls, timer, timer_set, end


if __name__ == "__main__":
    try:
        token = os.environ["telegram_token"]
    except KeyError:
        sys.exit("$telegram_token is not defined")

    user_urls = {}
    updater = Updater(token)

    updater.dispatcher.add_handler(CommandHandler('help', help_cmds))
    updater.dispatcher.add_handler(CommandHandler('add', wrap_handler(add, user_urls)))
    updater.dispatcher.add_handler(CommandHandler('remove', wrap_handler(remove, user_urls)))
    updater.dispatcher.add_handler(CommandHandler('list', wrap_handler(list_urls, user_urls)))
    updater.dispatcher.add_handler(CommandHandler('timer', wrap_handler(timer, user_urls)))
    updater.dispatcher.add_handler(CommandHandler('set_timer', wrap_handler(timer_set, user_urls)))
    updater.dispatcher.add_handler(CommandHandler('end', wrap_handler(end, user_urls)))

    updater.start_polling()
    updater.idle()
