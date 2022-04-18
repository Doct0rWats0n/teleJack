from teleJack.orm_db import start_bet, everyday_prize, base
from teleJack.bot import (
    TextGame, ImageGame,
    game_markup, game_type_markup, text_game_markup, img_game_markup
)
from teleJack.game_files import draw_statistics, States
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove, InputMediaPhoto
)
from telegram.ext import (
    Updater, Filters, CallbackContext,
    CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler
)
from telegram import Bot as TelegramBot
from telegram.error import Unauthorized
from io import BytesIO
from typing import Callable
import schedule
from threading import Thread


def check_exist(func: Callable) -> Callable:
    """Проверка существования пользователя в базе данных"""
    not_registered_message = '''
У вас нет игрового профиля.
Для его создания введите команду:
/start
    '''

    def new_func(self, upd: Update, cont: CallbackContext):
        chat_id = upd.message.chat_id
        if not base.check_if_player_exists(chat_id):
            upd.message.reply_text(not_registered_message)
            return
        return func(self, upd, cont)

    return new_func


class GamePart:
    """
    Класс, содержащий игровой функционал для бота
    """
    # Содержание сообщений в зависимости от статуса игры
    messages = {
        States.WIN: 'Вы выиграли! Ваш выигрыш начислен вам на счет',
        States.LOSE: 'Крупье выиграл. Повезет в другой раз',
        States.DRAW: 'Ничья. Вам возвращена стартовая ставка',
        States.BLACKJACK: 'У вас блэкджек! Вы выиграли!'
    }

    def __init__(self, dp, bot: TelegramBot):
        self.playing = {}  # Словарь со всеми играми, проходящими в текущий момент
        self.bot = bot  # Бот. Понадобится для ежедневного начисления бонуса

        commands = [
            ('game', self.choose_game)
        ]
        handlers = [CommandHandler(i, j) for i, j in commands]
        bet_conversation = ConversationHandler(
            entry_points=[CommandHandler('change_bet', self.change_request)],
            states={
                1: [MessageHandler(Filters.text & ~Filters.command, self.change_bet)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        handlers.append(bet_conversation)
        handlers.append(CallbackQueryHandler(self.query_handler))
        [dp.add_handler(handler) for handler in handlers]

        prize_thread = Thread(target=self.start_scheduler)
        prize_thread.start()

    def check_playing(func: Callable) -> Callable:
        """Проверка активного статуса игры у игрока"""
        def new_func(self, upd: Update, cont: CallbackContext):
            chat_id = upd.message.chat_id
            if chat_id in self.playing:
                upd.message.reply_text('Чтобы совершить это действие, необходимо завершить начатую игру.')
                return
            res = func(self, upd, cont)
            return res
        return new_func

    @check_exist
    @check_playing
    def choose_game(self, upd: Update, cont: CallbackContext) -> None:
        """Выбор режима игры"""
        upd.message.reply_text('Выберите режим игры.', reply_markup=game_type_markup)

    def everyday_prize_schedule(self):
        """Каждодневное начисление фиксированного бонуса на счет каждого игрока"""
        players = base.get_all_players()
        for player in players:
            base.add_everyday_bonus(player.id)
            try:
                self.bot.send_message(player.id, text=f'Вам начислен ежедневный бонус в размере {everyday_prize}.')
            except Unauthorized:
                base.remove_player(player.id)

    def start_scheduler(self):
        """Запуск каждодневного начисления. Нужно класть в поток"""
        schedule.every().day.at('00:00').do(self.everyday_prize_schedule)
        while True:
            schedule.run_pending()

    @check_playing
    def game(self, upd: Update, cont: CallbackContext) -> None:
        """Идентифицкация и начало игры"""
        chat_id = upd.message.chat_id
        res = base.subtract_user_bet(chat_id)  # Вычет игровой ставки для игрока
        if not res:
            upd.message.reply_text('''
            На балансе недостаточно средств для снятия ставки.
            Вы можете изменить ставку или подождать ежедневного бонуса.
            ''')
            return

        mode = cont.args[0]  # Получение режима игры, выбранного пользователем
        if mode == 'img':
            usergame = ImageGame()
            # Получение игровых колод и счета
            player_deck, player_score = usergame.get_deck('player'), usergame.get_count('player')
            dealer_deck, dealer_score = usergame.get_deck('dealer'), usergame.get_count('dealer')
            # Отправка сообщений с игрой и получение их id
            dealer_msg = upd.message.reply_photo(photo=dealer_deck, caption=dealer_score)
            player_msg = upd.message.reply_photo(photo=player_deck, caption=player_score, reply_markup=game_markup)
        else:
            usergame = TextGame()
            # Получение игровых колод и счета
            player_deck, player_score = usergame.get_deck('player'), usergame.get_count('player')
            dealer_deck, dealer_score = usergame.get_deck('dealer'), usergame.get_count('dealer')
            # Отправка сообщений с игрой и получение их id
            dealer_msg = upd.message.reply_text(dealer_deck + '\n' + dealer_score)
            player_msg = upd.message.reply_text(player_deck + '\n' + player_score, reply_markup=game_markup)

        player_id, dealer_id = player_msg.message_id, dealer_msg.message_id
        self.playing[chat_id] = {'player': player_id, 'dealer': dealer_id, 'game': usergame}
        if usergame.get_state('player') == 'BJ':
            # Пока что костыль вставил, но надо грамотно
            # поработать с ситуацией, когда и у игрока, и у крупье выпадает блэкджек
            usergame.game.add_dealer_card()
            if usergame.game.dealer.get_len_hand() == 2 and usergame.get_count('dealer') == 21:
                self.skip(upd, cont)
            else:
                del usergame.game.dealer.hand[1:]
                self.count_results(upd, cont)

    def take(self, upd: Update, cont: CallbackContext) -> None:
        """Реализация хода игрока"""
        chat_id = upd.message.chat_id
        if not (chat_id in self.playing):  # чисто дебаг функция, можно удалить
            print(f'Пользователь {cont.bot.username};{chat_id} вне списка игроков')
            return

        player_id = self.playing[chat_id]['player']
        usergame = self.playing[chat_id]['game']
        usergame.add_card()
        player_deck, player_score = usergame.get_deck('player'), usergame.get_count('player')
        # Изменение содержания прежних сообщений на обновленные
        if isinstance(usergame, TextGame):
            cont.bot.edit_message_text(player_deck + '\n' + player_score, chat_id, player_id, reply_markup=game_markup)
        else:
            cont.bot.edit_message_media(chat_id=chat_id, message_id=player_id, media=InputMediaPhoto(player_deck))
            cont.bot.edit_message_caption(chat_id=chat_id, message_id=player_id, caption=player_score,
                                          reply_markup=game_markup)

        # Если у игрока полная рука, симулирует пропуск хода
        # Если у игрока перебор, заканчивает игру
        if usergame.get_state('player') == 'MORE':
            self.count_results(upd, cont)
        elif usergame.is_player_hand_full():
            self.skip(upd, cont)

    def skip(self, upd: Update, cont: CallbackContext) -> None:
        """Реализация пропуска хода"""
        chat_id = upd.message.chat_id
        if chat_id not in self.playing:  # чисто дебаг функция, можно удалить
            print(f'Пользователь {cont.bot.username};{chat_id} вне списка игроков')
            return

        dealer_id = self.playing[chat_id]['dealer']
        usergame: TextGame | ImageGame = self.playing[chat_id]['game']
        usergame.dealer_turn()

        dealer_deck, dealer_score = usergame.get_deck('dealer'), usergame.get_count('dealer')
        # Изменение содержания прежних сообщений на обновленные
        if isinstance(usergame, TextGame):
            cont.bot.editMessageText(dealer_deck + '\n' + dealer_score, chat_id, dealer_id)
        else:
            cont.bot.edit_message_media(chat_id=chat_id, message_id=dealer_id, media=InputMediaPhoto(dealer_deck))
            cont.bot.edit_message_caption(chat_id=chat_id, message_id=dealer_id, caption=dealer_score)
        # Завершение игры и подсчет результатов
        self.count_results(upd, cont)

    def count_results(self, upd: Update, cont: CallbackContext) -> None:
        """Подсчет результатов и завершение игры"""
        chat_id = upd.message.chat_id
        player_id = self.playing[chat_id]['player']
        usergame: TextGame | ImageGame = self.playing[chat_id]['game']
        res = usergame.get_result()
        # Выбор игровой раскладки с кнопкой "Новая игра"
        if isinstance(usergame, TextGame):
            new_game_markup = text_game_markup
        else:
            new_game_markup = img_game_markup
        upd.message.reply_text(self.messages[res], reply_markup=new_game_markup)
        # Удаление игровой клавиатуры у сообщения с завершенной игрой
        self.clear_message(cont, chat_id, player_id)
        base.game_result(chat_id, res)
        del self.playing[chat_id]

    def change_bet(self, upd: Update, cont: CallbackContext) -> ConversationHandler.END:
        """Обновление пользовательской ставки. Вызывается из change_request"""
        chat_id = upd.message.chat_id
        if chat_id in self.playing:
            upd.message.reply_text('Нельзя менять ставку во время игры.')
            return ConversationHandler.END

        try:
            new_bet = int(upd.message.text)
            mess = base.change_user_bet(chat_id, new_bet)
            if not mess:
                mess = 'Ставка успешно изменена.'
        except (TypeError, ValueError):
            upd.message.reply_text('Неверные данные. Введите целое число.')
            return 1
        upd.message.reply_text(mess)
        return ConversationHandler.END

    def change_request(self, upd: Update, cont: CallbackContext) -> int:
        """Запрос на изменени игровой ставки"""
        chat_id = upd.message.chat_id
        if chat_id in self.playing:
            upd.message.reply_text('Нельзя менять ставку во время игры.')
            return ConversationHandler.END
        upd.message.reply_text(
            f'Введите целое число для изменения ставки (минимум - {start_bet}. Для отмены введите /cancel'
        )
        return 1

    def cancel(self, upd: Update, cont: CallbackContext) -> ConversationHandler.END:
        """Отмена изменения ставки. Вызывается после вызова change_request"""
        upd.message.reply_text('Операция отменена.')
        return ConversationHandler.END

    def clear_message(self, cont: CallbackContext, chat_id: int, mes_id: int) -> None:
        """Удаляет клавиатуру у сообщения с завершенной игрой"""
        cont.bot.edit_message_reply_markup(chat_id=chat_id, message_id=mes_id)

    def query_handler(self, upd: Update, cont: CallbackContext) -> None:
        """Обработчик кнопок на игровой клавиатуре"""
        query = upd.callback_query
        query.answer()

        if query.data == 'take':  # Взять карту
            self.take(query, cont)
        elif query.data == 'skip':  # Пропустить ход
            self.skip(query, cont)
        elif query.data == 'new_text':  # Новая игра в текстовом режиме
            cont.args = ['text']
            self.game(query, cont)
        elif query.data == 'new_img':  # Новая игра в графическом режиме
            cont.args = ['img']
            self.game(query, cont)


class ShopPart:
    """
    Класс, ответственный за функционал магазина карт
    """
    def __init__(self, dp):
        commands = [
            ()
        ]
        handlers = [CommandHandler(i, j) for i, j in commands]
        [dp.add_handler(handler) for handler in handlers]

    def start_shop(self, upd: Update, cont: CallbackContext):
        pass


class MainPart:
    """
    Основной функционал бота
    """
    help_text = f"""
Мои команды:
    /game - выбрать режим игры и сыграть партию (режим можно сменить после завершения партии);
    /money - вывести средства на счете;
    /bet  - вывести игровую ставку (по умолчанию {start_bet});
    /change_bet - изменить игровую ставку (не должна быть меньше {start_bet} и превышать баланс средств);
    /stat - вывести статистику игрока за все время;
    /help - вывести эту подсказку.

По вопросам и багрепортам:
    @another_conformist / @irealized
    """

    def __init__(self, dp):
        commands = [
            ('bet', self.get_bet), ('money', self.get_money), ('stat', self.get_stat),
            ('help', self.help_message), ('start', self.start)
        ]
        handlers = [CommandHandler(i, j) for i, j in commands]
        handlers.append(MessageHandler(Filters.all, self.wrong_command))
        [dp.add_handler(handler) for handler in handlers]

    @check_exist
    def get_bet(self, upd: Update, cont: CallbackContext) -> None:
        """Получение ставки игрока"""
        chat_id = upd.message.chat_id
        user_bet = base.get_user_bet(chat_id)
        upd.message.reply_text(user_bet)

    @check_exist
    def get_money(self, upd: Update, cont: CallbackContext) -> None:
        """Получение средств на профиле игрока"""
        chat_id = upd.message.chat_id
        money = base.get_user_money(chat_id)
        upd.message.reply_text(f'Баланс: {money}.')

    @check_exist
    def get_stat(self, upd: Update, cont: CallbackContext) -> None:
        """Получение статистики игрока в графическом виде"""
        chat_id = upd.message.chat_id
        user_stat = base.get_player_statistics(chat_id)
        photo = cont.bot.get_user_profile_photos(chat_id, limit=1).photos[0]
        data = cont.bot.getFile(photo[-1].file_id)
        normal_photo = BytesIO(data.download_as_bytearray())
        stat_photo = draw_statistics(user_stat, normal_photo, upd.message.chat.full_name)
        upd.message.reply_photo(stat_photo)

    def help_message(self, upd: Update, cont: CallbackContext) -> None:
        """Получение сообщения-подсказки"""
        upd.message.reply_text(self.help_text)

    def wrong_command(self, upd: Update, cont: CallbackContext) -> None:
        """Обработчик нераспознаваемой команды игрока"""
        upd.message.reply_text('Не знаю такой команды. Для получения всех команд введите команду /help')

    def start(self, upd: Update, cont: CallbackContext) -> None:
        """
        Команда для создания профиля игрока в базе

        Вызывается лишь один раз для создания профиля
        Обязательно должна быть первой командой, введенной игроком
        """
        chat_id = upd.message.chat_id
        if base.check_if_player_exists(chat_id):
            message = 'Для игры введите команду /game\nЧтобы вывести справку, введите /help'
            upd.message.reply_text(message)
            return
        message = 'Привет! Я - телеграм бот, устраивающий партии в блэкджек.' + self.help_text
        base.add_player(chat_id)
        upd.message.reply_text(message)


class Bot:
    """
    Класс главного бота
    """
    def __init__(self, token):
        self.token = token

    def start_bot(self) -> None:
        """Запуск бота"""
        upd = Updater(self.token, use_context=True)
        dp = upd.dispatcher
        GamePart(dp, upd.bot)
        MainPart(dp)

        upd.start_polling()
        upd.idle()
