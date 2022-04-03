from .data import get_session, Player, Statistics, start_bet, start_money
from teleJack.game_files import States


class Controller:
    def __init__(self):
        self.sess = get_session()

    def add_player(self, player_id: int) -> None:
        """Добавляет игрока в базу данных"""
        new_player = Player(id=player_id)
        new_stat = Statistics(id=player_id)
        self.sess.add(new_player)
        self.sess.add(new_stat)
        self.sess.commit()

    def check_if_player_exists(self, player_id: int) -> bool:
        """Проверка на наличие игрока в базе данных"""
        if not self.get_player(player_id):
            return False
        return True

    def remove_player(self, player_id: int) -> None:
        """Удаление игрока из базы данных"""
        player = self.get_player(player_id)
        statistics = self.get_statistics(player_id)
        self.sess.delete(player)
        self.sess.delete(statistics)
        self.sess.commit()

    def get_player(self, player_id: int) -> Player:
        """Получение объекта Player из базы данных"""
        player = self.sess.query(Player).get(player_id)
        return player

    def get_statistics(self, player_id: int) -> Statistics:
        """Получение объекта Statistics из базы данных"""
        stat = self.sess.query(Statistics).get(player_id)
        return stat

    def get_user_money(self, player_id: int) -> int:
        """Получение денег, имеющихся у игрока"""
        player = self.get_player(player_id)
        return player.money_count

    def get_user_bet(self, player_id: int) -> int:
        """Получение ставки игрока"""
        player = self.get_player(player_id)
        return player.game_bet

    def subtract_user_bet(self, player_id: int) -> bool:
        """Вычитание ставки из денег игрока в начале игры"""
        player = self.get_player(player_id)
        if player.money_count < player.game_bet:
            return False
        player.money_count -= player.game_bet
        self.sess.commit()
        return True

    def get_player_statistics(self, player_id) -> dict:
        stat = self.get_statistics(player_id)
        return stat.get_stat()

    def change_user_bet(self, player_id: int, new_bet: int) -> str:
        """Смена игровой ставки"""
        player = self.get_player(player_id)
        if player.money_count < new_bet:
            return 'Новая ставка превышает средства на счете'
        elif new_bet < start_bet:
            return f'Новая ставка меньше минимальной (минимальная - {start_bet})'
        player.game_bet = new_bet
        self.sess.commit()

    def update_user_money(self, player_id: int, operation: str) -> None:
        """Обновление денег на счете пользователя"""
        player = self.get_player(player_id)
        if operation == States.DRAW:
            player.money_count += player.game_bet
        elif operation == States.WIN:
            player.money_count += player.game_bet * 2
        elif operation == States.BLACKJACK:
            player.money_count += player.game_bet * 2.5
        self.sess.commit()

    def game_result(self, player_id, result) -> None:
        """Обновляет счет игрока и его статистику, основываясь на результате игры"""
        self.update_user_money(player_id, result)
        self.update_user_statistics(player_id, result)

    def update_user_statistics(self, player_id: int, game_status: str) -> None:
        """Обновление пользовательской статистики"""
        stat: Statistics = self.get_statistics(player_id)
        money = self.get_user_bet(player_id)
        if game_status == States.LOSE:
            stat.lose_game += 1
            stat.lose_money += money
        elif game_status == States.WIN:
            stat.win_game += 1
            stat.win_money += money
        elif game_status == States.BLACKJACK:
            stat.win_game += 1
            stat.blackjack_game += 1
            stat.win_money += money * 1.5
        else:
            stat.draw_game += 1

        balance = self.get_user_money(player_id)
        if balance > stat.money_record:
            stat.money_record = balance

        stat.game_played += 1
        self.sess.commit()
