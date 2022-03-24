from .data import db_session
from .data.player import Player
from .data.player_stat import Statistics


class Controller:
    def __init__(self):
        self.sess = db_session.get_session()

    def add_player(self, player_id: int):
        """Добавляет игрока в базу данных"""
        new_player = Player(id=player_id)
        new_stat = Statistics(id=player_id)
        self.sess.add(new_player)
        self.sess.add(new_stat)
        self.sess.commit()

    def check_if_player_exists(self, player_id: int):
        """Проверка на наличие игрока в базе данных"""
        if not self.get_player(player_id):
            return False
        return True

    def remove_player(self, player_id: int):
        """Удаление игрока из базы данных"""
        player = self.get_player(player_id)
        statistics = self.get_statistics(player_id)
        self.sess.delete(player)
        self.sess.delete(statistics)
        self.sess.commit()

    def get_player(self, player_id: int):
        """Получение объекта Player из базы данных"""
        player = self.sess.query(Player).get(player_id)
        return player

    def get_statistics(self, player_id: int):
        """Получение объекта Statistics из базы данных"""
        stat = self.sess.query(Statistics).get(player_id)
        return stat

    def get_user_money(self, player_id: int):
        """Получение денег, имеющихся у игрока"""
        player = self.get_player(player_id)
        return player.money_count

    def get_user_bet(self, player_id: int):
        """Получение ставки игрока"""
        player = self.get_player(player_id)
        return player.game_bet

    # def subtract_bet(self, player_id: int):
    #     """Вычитание ставки из денег игрока в начале игры"""
    #     player = self.get_player(player_id)
    #     if player.money_count < player.game_bet:
    #         return False
    #     player.money_count -= player.game_bet
    #     self.sess.commit()
    #     return True
    def get_player_statistics(self, player_id):
        stat = self.get_statistics(player_id)
        return stat.get_stat()

    def change_bet(self, player_id: int, new_bet: int):
        """Смена игровой ставки"""
        player = self.get_player(player_id)
        if player.money_count < new_bey:
            return False
        player.game_bet = new_bet
        self.sess.commit()
        return True

    def update_user_money(self, player_id: int, operation: str):
        """Обновление денег на счете пользователя"""
        player = self.get_player(player_id)
        bet = self.get_user_bet(player_id)
        if operation == '-':
            player.money_count -= bet
        elif operation == '+':
            player.money_count += bet
        else:
            player.money_count += bet * 2
        self.sess.commit()

    def update_user_statistics(self, player_id: int, game_status: str):
        """Обновление пользовательской статистики"""
        stat: Statistics = self.get_statistics(player_id)
        money = self.get_user_bet(player_id)
        if game_status == '+':
            stat.lose_game += 1
            stat.lose_money += money
        elif game.status == '+':
            stat.win_game += 1
            stat.win_money += money
        else:
            stat.draw_game += 1
        stat.game_played += 1
        self.sess.commit()
