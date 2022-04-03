from teleJack.orm_db import Controller, global_init, start_bet
from teleJack.bot import TextGame, ImageGame, BASE_PATH
from teleJack.game_files import draw_statistics, States
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove, InputMediaPhoto
)
from telegram.ext import (
    Updater, Filters, CallbackContext,
    CommandHandler, MessageHandler, CallbackQueryHandler
)
from io import BytesIO

global_init(BASE_PATH)
base = Controller()  # База данных

game_keyboard = [
    [
        InlineKeyboardButton(text='Взять', callback_data='take'),
        InlineKeyboardButton(text='Пас', callback_data='skip')
     ]
]
game_markup = InlineKeyboardMarkup(game_keyboard)  # Основная игровая клавиатура

text_keyboard = [
    [
        InlineKeyboardButton(text='Новая игра', callback_data='new_text')
    ]
]
text_game_markup = InlineKeyboardMarkup(text_keyboard)  # Клавиатура для новой игры в текстовом режиме

img_keyboard = [
    [
        InlineKeyboardButton(text='Новая игра', callback_data='new_img')
    ]
]
img_game_markup = InlineKeyboardMarkup(img_keyboard)  # Клавиатура для новой игры в графическом режиме


def check_exist(func):
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

    def __init__(self, dp):
        self.playing = {}  # словарь со всеми играми, проходящими в текущий момент

        commands = [
            ('change_bet', self.change_bet), ('game', self.game)
        ]
        handlers = [CommandHandler(i, j) for i, j in commands]
        handlers.append(CallbackQueryHandler(self.query_handler))
        [dp.add_handler(handler) for handler in handlers]

    @check_exist
    def game(self, upd: Update, cont: CallbackContext) -> None:
        """Идентифицкация и начало игры"""
        chat_id = upd.message.chat_id
        if chat_id in self.playing:
            upd.message.reply_text('Чтобы начать новую игру, необходимо закончить предыдущую.')
            return
        res = base.subtract_user_bet(chat_id)  # Вычет игровой ставки для игрока
        if not res:
            upd.message.reply_text('''
            На балансе недостаточно средств для снятия ставки.
            Вы можете изменить ставку или подождать ежедневного бонуса.
            ''')
            return

        try:
            mode = cont.args[0]  # Получение режима игры, выбранного пользователем
            if mode == 'img':
                usergame = ImageGame()
                # Получение игровых колод и счета
                player_deck, player_score = usergame.get_deck('player'), usergame.get_count('player')
                dealer_deck, dealer_score = usergame.get_deck('dealer'), usergame.get_count('dealer')
                # Отправка сообщений с игрой и получение их id
                dealer_msg = upd.message.reply_photo(photo=dealer_deck, caption=dealer_score)
                player_msg = upd.message.reply_photo(photo=player_deck, caption=player_score, reply_markup=game_markup)
            elif mode == 'text':
                usergame = TextGame()
                # Получение игровых колод и счета
                player_deck, player_score = usergame.get_deck('player'), usergame.get_count('player')
                dealer_deck, dealer_score = usergame.get_deck('dealer'), usergame.get_count('dealer')
                # Отправка сообщений с игрой и получение их id
                dealer_msg = upd.message.reply_text(dealer_deck + '\n' + dealer_score)
                player_msg = upd.message.reply_text(player_deck + '\n' + player_score, reply_markup=game_markup)
            else:
                raise ValueError  # Вызывает ошибку, если пользователь неверно указал режим
        except ValueError:
            upd.message.reply_text('Неправильно выбран режим игры')
            return
        except IndexError:
            upd.message.reply_text('Неправильное использование команды.')
            return

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
        if usergame.is_player_hand_full():
            self.skip(upd, cont)
        # Если у игрока перебор, заканчивает игру
        elif usergame.get_state('player') == 'MORE':
            self.count_results(upd, cont)

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

    @check_exist
    def change_bet(self, upd: Update, cont: CallbackContext) -> None:
        """Смена игровой ставки"""
        chat_id = upd.message.chat_id
        # Если игра уже идет, ставку изменить нельзя
        if chat_id in self.playing:
            upd.message.reply_text('Нельзя менять ставку во время игры.')
            return
        try:
            new_bet = int(cont.args[0])
            mess = base.change_user_bet(chat_id, new_bet)
            if not mess:
                mess = 'Ваша ставка успешно изменена.'
        except (IndexError, TypeError, ValueError):
            mess = 'Неверное использование команды.'
        upd.message.reply_text(mess)

    def clear_message(self, cont: CallbackContext, chat_id: int, mes_id: int) -> None:
        """Удаляет клавиатуру у сообщения с завершенной игрой"""
        cont.bot.edit_message_reply_markup(chat_id=chat_id, message_id=mes_id)

    def query_handler(self, upd: Update, cont: CallbackContext) -> None:
        """Обработчик кнопок на игровой клавиатуре"""
        query = upd.callback_query
        query.answer()

        if query.data == 'take':
            self.take(query, cont)
        elif query.data == 'skip':
            self.skip(query, cont)
        elif query.data == 'new_text':
            cont.args = ['text']
            self.game(query, cont)
        elif query.data == 'new_img':
            cont.args = ['img']
            self.game(query, cont)


class MainPart:
    """
    Основной функционал бота
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
        message = f'''
Мои команды:
    /game *режим* - начать игру (предыдущая игра должна быть завершена). Режимы - img и text
    /money - вывести средства на счете
    /bet  - вывести игровую ставку (по умолчанию {start_bet}
    /change_bet *число* - изменить игровую ставку (не должна быть меньше {start_bet} и превышать баланс средств
    /stat - вывести статистику игрока за все время
    /help - вывести эту подсказку

По вопросам и багрепортам:
    @another_conformist / @irealized
        '''
        upd.message.reply_text(message)

    def wrong_command(self, upd: Update, cont: CallbackContext) -> None:
        """Обработчик нераспознаваемой команды игрока"""
        upd.message.reply_text('Не знаю такой команды. Для получения всех команд введите команду /help')

    def start(self, upd: Update, cont: CallbackContext) -> None:
        """
        Команда для создания профиля игрока в базе

        Вызывается лишь один раз для создания профиля
        Обязательна должна быть первой командой, введенной игроком
        """
        chat_id = upd.message.chat_id
        if base.check_if_player_exists(chat_id):
            message = 'Для игры введите команду /game\nЧтобы вывести справку, введите /help'
            upd.message.reply_text(message)
            return
        message = f'''
Привет! Я - телеграм бот, устраивающий партии в блэкджек.

Мои команды:
    /money - вывести средства на счете.
    /bet  - вывести игровую ставку (по умолчанию {start_bet}.
    /change_bet *число* - изменить игровую ставку.
    Ставка не должна быть меньше {start_bet} и превышать баланс средств.
    /stat - вывести статистику игрока за все время.
    /help - вывести эту подсказку.

По вопросам и багрепортам:
    @another_conformist / @irealized
        '''
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
        GamePart(dp)
        MainPart(dp)

        upd.start_polling()
        upd.idle()
