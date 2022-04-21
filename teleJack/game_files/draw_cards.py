from PIL import Image, ImageDraw
from io import BytesIO
import requests
from teleJack.logging import init_log
import os

table_path = 'teleJack/static/imgs/table2.png'
cards_path = 'teleJack/static/cards'
table_image = Image.open(table_path)
x, y = 40, 135
positions = [(x + i * 250, y) for i in range(5)]


@init_log
def get_images_from_url():
    m = [Image.open(BytesIO(requests.get('https://picsum.photos/1284/600').content)) for _ in range(5)]
    for n, img in enumerate(m):
        with BytesIO() as output:
            img.save(output, format='JPEG', quality=40)
            m[n] = Image.open(output).copy()
    return m


@init_log
def load_cards():
    cards = {}
    for dir_name, _, files in os.walk(cards_path):
        d = dir_name.replace('\\', '/')
        for file in files:
            cards[f'{d}/{file}'] = Image.open(f'{d}/{file}')
    return cards


table_images_from_url = get_images_from_url()
cards = load_cards()


def resize_image(image: Image.Image) -> Image.Image:
    width, height = image.size
    o = height / width
    r_image = image.resize((200, int(200 * o)))
    return r_image


class Board:
    def __init__(self, start_cards=False, table=table_image):
        # self.table = Image.open(table_path)  # Открывает фотографию с игровым столом
        self.table = table.copy()
        self.cards_count = 0

        if start_cards:  # Добавляет карты, если они есть
            [self.add_card(card) for card in start_cards]

    def add_card(self, path_to_card: str) -> bytes:
        """Наносит картинку карты на игровой стол"""
        card = cards[path_to_card]
        card = resize_image(card)
        self.table.paste(card, positions[self.cards_count])
        self.cards_count += 1
        return self.get_table()

    def get_table(self) -> bytes:
        """Выдает картинку в байтах"""
        with BytesIO() as output:
            # self.table.save(output, 'JPEG')
            self.table.save(output, 'PNG')
            data = output.getvalue()
        return data
