from .db_session import SqlAlchemyBase
import sqlalchemy
from sqlalchemy import orm
from datetime import datetime
from .start_values import start_money, start_bet, start_deck


class Player(SqlAlchemyBase):

    __tablename__ = 'players'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    money_count = sqlalchemy.Column(sqlalchemy.Integer, default=start_money)
    game_bet = sqlalchemy.Column(sqlalchemy.Integer, default=start_bet)
    register_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now)

    statistics = orm.relation('Statistics', back_populates='player')
    decks = orm.relation('PlayerDecks', back_populates='player')

    def __repr__(self):
        return f'{self.id} - id, {self.money_count} - имеющихся денег, {self.game_bet} - ставка'
