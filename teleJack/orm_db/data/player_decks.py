from .db_session import SqlAlchemyBase
import sqlalchemy
from sqlalchemy import orm


class PlayerDecks(SqlAlchemyBase):
    __tablename__ = 'playerdecks'

    id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('players.id'), primary_key=True)
    chosen_deck = sqlalchemy.Column(sqlalchemy.Integer, default=1)
    available_decks = sqlalchemy.Column(sqlalchemy.String, default='1')

    player = orm.relation('Player')

    def __repr__(self):
        return f'ID - {self.id}, Выбранная колода - {self.chosen_deck}, Доступные колоды - {self.available_decks}'
