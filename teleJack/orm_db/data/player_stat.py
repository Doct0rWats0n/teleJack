from .db_session import SqlAlchemyBase
from .player import Player
import sqlalchemy
from sqlalchemy import orm


class Statistics(SqlAlchemyBase):
    __tablename__ = 'statistics'

    id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('players.id'), primary_key=True)
    game_played = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    win_game = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    lose_game = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    draw_game = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    blackjack_game = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    win_money = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    lose_money = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    money_record = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    player = orm.relation('Player')

    def get_stat(self) -> dict:
        """Выдает статистику игрока в удобном формате"""
        stat = {
            'Сыгранных игр': self.game_played,
            'Выигранных игр': self.win_game,
            'Проигранных игр': self.lose_game,
            'Ничьих': self.draw_game,
            'Игр с блэкджеком': self.blackjack_game,
            'Выиграно денег': self.win_money,
            'Проиграно денег': self.lose_money,
            'Рекордный выигрыш': self.money_record
        }
        return stat
