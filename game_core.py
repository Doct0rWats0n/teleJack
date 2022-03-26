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
    
    def shuffle(self):
        self.cards = [Card(nominal, suit) for nominal in CardNominal for suit in CardSuit for i in range(3)]
        self.cards.sort(key=lambda x: random.random())

    def take_card(self) -> Card:
        return self.cards.pop()


class Player:
    def __init__(self):
        self.hand = []

    def take_card(self, card: Card):
        self.hand.append(card)

    def count_card(self) -> int:
        count = 0
        for card in self.hand:
            if card.nominal in (CardNominal.Jack, CardNominal.Queen, CardNominal.King):
                count += 10
            if card.nominal == CardNominal.Ace:
                if count + 11 > 21:
                    count += 1
                else:
                    count += 11
            else:
                match card.nominal:
                    case CardNominal.Two:
                        count += 2
                    case CardNominal.Three:
                        count += 3
                    case CardNominal.Four:
                        count += 4
                    case CardNominal.Five:
                        count += 5
                    case CardNominal.Six:
                        count += 6
                    case CardNominal.Seven:
                        count += 7
                    case CardNominal.Eight:
                        count += 8
                    case CardNominal.Nine:
                        count += 9
                    case CardNominal.Ten:
                        count += 10
        return count


class Dealer(Player):
    def __init__(self):
        super().__init__()


class Game:
    def __init__(self, bet: int):
        self.bet = bet
        self.player = Player()
        self.dealer = Dealer()
        self.card_deck = CardDeck()
        self.start()

    def start(self):
        for i in range(2):
            self.player.take_card(self.card_deck.take_card())
        self.dealer.take_card(self.card_deck.take_card())

    def add_player_card(self):
        self.player.take_card(self.card_deck.take_card())

    def add_dealer_card(self):
        while self.dealer.count_card() < 17:
            self.dealer.take_card(self.card_deck.take_card())
