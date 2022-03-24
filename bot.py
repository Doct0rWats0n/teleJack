from orm_db.base_control import Controller   # лишний импорт, добавил лишь для простоты тестирования
from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler
import config


class Bot:
    def __init__(self, token):
        self.token = token

    def start(self, update: Update, context: CallbackContext):
        pass

    def start_bot(self):
        upd = Updater(self.token, use_context=True)
        dp = upd.dispatcher

        dp.add_handler(CommandHandler('start', self.start))
        upd.start_polling()
        upd.idle()
