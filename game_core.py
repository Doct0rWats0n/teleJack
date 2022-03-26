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


class CardDeck:
    def __init__(self):
        self.cards = list()
        self.shuffle()
    
    def shuffle(self):
        self.cards = [Card(nominal, suit) for nominal in CardNominal for suit in CardSuit for i in range(3)]
        self.cards.sort(key=lambda x: random.random())

    def take_card(self) -> Card:
        return self.cards.pop()
