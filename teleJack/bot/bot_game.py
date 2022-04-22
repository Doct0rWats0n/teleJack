import random

from teleJack.game_files import Game
from teleJack.game_files import Board, table_images_from_url
from teleJack.bot import States


text_suit = {
    'Spades': '♠',
    'Diamonds': '♦',
    'Hearts': '♥',
    'Clubs': '♣',
}
text_nominal = {
    'Two': '2', 'Three': '3', 'Four': '4', 'Five': '5', 'Six': '6',
    'Seven': '7', 'Eight': '8', 'Nine': '9', 'Ten': '10',
    'Jack': 'J', 'Queen': 'Q', 'King': 'K', 'Ace': 'A'
}


def check_player_dealer(func):
    """Проверка правильности передаваемого аргумента"""
    def new_func(self, who):
        if who not in ['player', 'dealer']:
            raise ValueError(f'Неверный аргумент: {who}')
        return func(self, who)

    return new_func


class StandardGame:
    def __init__(self):
        self.game = Game()

    @check_player_dealer
    def get_state(self, who: str) -> str:
        """Получение текущего игрового статуса игрока или крупье"""
        if who == 'player':
            score = self.game.player.count_card()
        else:
            score = self.game.dealer.count_card()

        if score == 21:
            return 'BJ'
        elif score > 21:
            return 'MORE'
        else:
            return 'LESS'

    @check_player_dealer
    def get_count(self, who: str) -> int:
        """Получение количества очков у игрока или крупье"""
        if who == 'player':
            count = f'Количество очков: {self.game.player.count_card()}'
        else:
            count = f'Количество очков у дилера: {self.game.dealer.count_card()}'
        return count

    def get_result(self) -> None:
        """Подсчет игрового результата"""
        userscore = self.game.player.count_card()
        dealerscore = self.game.dealer.count_card()

        if userscore > 21:
            res = States.LOSE
        elif dealerscore > 21:
            res = States.WIN
        elif userscore == 21 and self.game.player.get_len_hand() == 2:
            if self.game.dealer.get_len_hand() == 2 and self.game.dealer.count_card() == 21:
                res = States.DRAW
            else:
                res = States.BLACKJACK
        elif userscore > dealerscore:
            res = States.WIN
        elif userscore < dealerscore:
            res = States.LOSE
        elif userscore == dealerscore:
            res = States.DRAW
        return res

    def is_player_hand_full(self) -> bool:
        """Проверка заполнения руки игрока"""
        if self.game.player.get_len_hand() == 5:
            return True
        return False


class ImageGame(StandardGame):
    """
    Класс для проведения игры в графическом режиме
    """
    def __init__(self, card_pack='standard', table_from_url=True):
        super().__init__()
        self.card_pack = card_pack
        if not table_from_url:
            self.player_board = Board(self.get_path_to_cards(self.game.player.get_hand()))
            self.dealer_board = Board(self.get_path_to_cards(self.game.dealer.get_hand()))
        else:
            table = random.choice(table_images_from_url)
            self.player_board = Board(self.get_path_to_cards(self.game.player.get_hand()), table=table)
            self.dealer_board = Board(self.get_path_to_cards(self.game.dealer.get_hand()), table=table)

    def add_card(self) -> bool:
        """
        Добавление карты в колоду.

        Если у игрока уже есть 5 карт, не берет карту и возвращает False
        В ином случае, берет карту и возвращает True
        """
        if self.is_player_hand_full():
            return False
        card = self.game.add_player_card()
        path = self.get_path_to_cards([card])[0]
        self.player_board.add_card(path)
        return True

    def dealer_turn(self) -> None:
        """Ход крупье"""
        self.game.add_dealer_card()
        [self.dealer_board.add_card(i) for i in self.get_path_to_cards(self.game.dealer.get_hand()[1:])]

    def get_path_to_cards(self, cards: list) -> list:
        """Получение пути до картинок переданных карт"""
        paths = [f'teleJack/static/cards/{self.card_pack}/{card.suit.name}/{card.nominal.name}.png' for card in cards]
        return paths

    @check_player_dealer
    def get_deck(self, who: str) -> bytes:
        """Получение колоды игрока или крупье"""
        if who == 'player':
            deck = self.player_board.get_table()
        else:
            deck = self.dealer_board.get_table()
        return deck


class TextGame(StandardGame):
    """
    Класс для проведения игры в текстовом режиме
    """
    def __init__(self):
        super().__init__()
        self.player_board = self.translate_cards(self.game.player.get_hand())
        self.dealer_board = self.translate_cards(self.game.dealer.get_hand())
        self.dealer_board.append('?')

    def translate_cards(self, cards: list) -> list:
        """Перевод переданных карт в текстовый режим"""
        translated = [f'{text_suit[card.suit.name]}{text_nominal[card.nominal.name]}' for card in cards]
        return translated

    def add_card(self) -> bool:
        """
        Добавление карты в колоду.

        Если у игрока уже есть 5 карт, не берет карту и возвращает False
        В ином случае, берет карту и возвращает True
        """
        if self.is_player_hand_full():
            return False
        card = self.game.add_player_card()
        card = self.translate_cards([card])
        self.player_board.extend(card)
        return True

    def dealer_turn(self) -> None:
        """Ход крупье"""
        self.game.add_dealer_card()
        self.dealer_board = self.translate_cards(self.game.dealer.get_hand())

    @check_player_dealer
    def get_deck(self, who: str) -> str:
        """Получение колоды игрока или крупье"""
        if who == 'player':
            deck = '  '.join(self.player_board)
        else:
            deck = '  '.join(self.dealer_board)
        return deck
