import random
from enum import Enum


class CardNominal(Enum):
    Two = 0
    Three = 1
    Four = 2
    Five = 3
    Six = 4
    Seven = 5
    Eight = 6
    Nine = 7
    Ten = 8
    Jack = 9
    Queen = 10
    King = 11
    Ace = 12


class CardSuit(Enum):
    Spades = 0
    Clubs = 1
    Hearts = 2
    Diamonds = 3


class Card:
    def __init__(self, nominal: CardNominal, suit: CardSuit):
        self.suit = suit
        self.nominal = nominal

    def __repr__(self):
        return f'{self.suit} {self.nominal}'


class CardDeck:
    def __init__(self):
        self.shuffle()
    
    def shuffle(self) -> None:
        """Перемешка колоды"""
        self.cards = [Card(nominal, suit) for nominal in CardNominal for suit in CardSuit for i in range(3)]
        self.cards.sort(key=lambda x: random.random())

    def take_card(self) -> Card:
        """Взятие карты из колоды"""
        return self.cards.pop()


class Player:
    def __init__(self):
        self.hand = []

    def take_card(self, card: Card) -> None:
        """Взятие карты"""
        self.hand.append(card)

    def count_card(self) -> int:
        """Подсчет количества очков у игрока"""
        count = 0
        aces = 0
        for card in self.hand:
            if card.nominal in (CardNominal.Jack, CardNominal.Queen, CardNominal.King):
                count += 10
            if card.nominal == CardNominal.Ace:
                aces += 1
            else:
                if card.nominal == CardNominal.Two:
                    count += 2
                elif card.nominal == CardNominal.Three:
                    count += 3
                elif card.nominal == CardNominal.Four:
                    count += 4
                elif card.nominal == CardNominal.Five:
                    count += 5
                elif card.nominal == CardNominal.Six:
                    count += 6
                elif card.nominal == CardNominal.Seven:
                    count += 7
                elif card.nominal == CardNominal.Eight:
                    count += 8
                elif card.nominal == CardNominal.Nine:
                    count += 9
                elif card.nominal == CardNominal.Ten:
                    count += 10
        for i in range(aces):
            if count + 11 > 21:
                count += 1
            else:
                count += 11
        return count

    def get_hand(self) -> list:
        return self.hand

    def get_len_hand(self) -> int:
        """Получение количества карт в игровой руке"""
        return len(self.hand)


class Dealer(Player):
    def __init__(self):
        super().__init__()


class Game:
    def __init__(self):
        self.player = Player()
        self.dealer = Dealer()
        self.card_deck = CardDeck()
        self.start()

    def start(self):
        """Запуск игры"""
        for i in range(2):
            self.player.take_card(self.card_deck.take_card())
        self.dealer.take_card(self.card_deck.take_card())

    def add_player_card(self) -> Card:
        """Добавление карты игроку"""
        if self.dealer.get_len_hand() < 5:
            self.player.take_card(self.card_deck.take_card())
            return self.player.hand[-1]  # Возврат взятой карты

    def add_dealer_card(self) -> None:
        """Добавление карты крупье"""
        while self.dealer.count_card() < 17 and self.dealer.get_len_hand() < 5:
            self.dealer.take_card(self.card_deck.take_card())
