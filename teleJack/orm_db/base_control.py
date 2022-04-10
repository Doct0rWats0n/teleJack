from .data import (
    get_session, Player, Statistics, PlayerDecks, Decks,
    start_bet, start_money, everyday_prize
)
from teleJack.game_files import States


class Controller:
    def __init__(self):
        self.sess = get_session()
        self.decks = self.get_all_decks()

    def add_player(self, player_id: int) -> None:
        """Добавляет игрока в базу данных"""
        new_player = Player(id=player_id)
        new_stat = Statistics(player=new_player)
        new_player_decks = PlayerDecks(player=new_player)

        self.sess.add(new_player)
        self.sess.add(new_stat)
        self.sess.add(new_player_decks)
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

    def get_all_players(self) -> list:
        players = self.sess.query(Player).all()
        return players

    def get_statistics(self, player_id: int) -> Statistics:
        """Получение объекта Statistics из базы данных"""
        stat = self.sess.query(Statistics).get(player_id)
        return stat

    def get_player_decks(self, player_id: int) -> PlayerDecks:
        """Получение объекты PlayerDecks из базы данных"""
        player_decks = self.sess.query(PlayerDecks).get(player_id)
        return player_decks

    def get_all_decks(self):
        """Получение всех колод из таблицы Decks"""
        # НЕОБХОДИМ РЕФАКТОРИНГ
        # МОЖНО ВМЕСТО ID КАК КЛЮЧ СДЕЛАТЬ NAME КАК КЛЮЧ, ЧТО ГОРАЗДО УДОБНЕЕ
        decks = self.sess.query(Decks).all()
        formatted_decks = {
            deck.id: deck.to_dict(only=(
                'name', 'description', 'cost'
            )) for deck in decks
        }
        return formatted_decks

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

    def add_everyday_bonus(self, player_id: int):  # костыль - можно сделать один метод для всех игроков
        """Добавляет ежедневный бонус на счет игрока"""
        player = self.get_player(player_id)
        player.money_count += everyday_prize
        self.sess.commit()

    def get_player_statistics(self, player_id) -> dict:
        """Возвращает статистику игрока"""
        stat = self.get_statistics(player_id)
        return stat.get_stat()

    def get_available_decks(self, player_id):
        """Возвращает доступные игроку колоды"""
        player_decks = self.get_player_decks(player_id)
        available = map(int, player_decks.available_decks.split())
        available = {self.decks[i]['name']: i for i in available}
        return available

    def get_deck(self, player_id: int):
        """Возвращает текущую колоду игрока"""
        player_decks = self.get_player_decks(player_id)
        deck = self.decks[player_decks.chosen_deck]
        return deck

    def get_decks_to_buy(self, player_id):
        """Возвращает некупленные колоды для определенного игрока"""
        player_decks = self.get_player_decks(player_id)
        decks = {self.decks[i]: i for i in self.decks if str(i) not in player_decks.available_decks}
        return decks

    def get_deck_info(self, deck_id: int):
        """Возвращает информацию о колоде"""
        return self.decks[deck_id].description, self.decks[deck_id].cost

    def change_deck(self, player_id: int, deck_id: int):
        """Меняет текущую колоду игрока"""
        player_deck = self.get_player_decks(player_id)
        player_deck.chosen_deck = deck_id
        self.sess.commit()

    def buy_deck(self, player_id: int, deck_id: int):
        """Обрабатывает покупку новой колоды"""
        money = self.get_user_money(player_id)
        cost = self.decks[deck_id]['cost']
        if money - cost < 0:
            return False  # Если у игрока недостаточно денег для покупки, возвращает False
        money -= cost
        player_decks = self.get_player_decks(player_id)
        player_decks.available_decks += f' {deck_id}'
        return True

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
            money *= 1.25
        else:
            stat.draw_game += 1

        if money * 2 > stat.money_record:
            stat.money_record = int(money * 2)

        stat.game_played += 1
        self.sess.commit()
