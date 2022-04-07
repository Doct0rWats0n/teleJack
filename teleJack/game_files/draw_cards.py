from PIL import Image, ImageDraw
from io import BytesIO

table_path = 'static/imgs/table.png'
positions = [(40, 40), (290, 40), (540, 40), (790, 40), (1040, 40)]


def resize_image(image: Image.Image) -> Image.Image:
    width, height = image.size
    o = height/width
    r_image = image.resize((190, int(190 * o)))
    return r_image


class Board:
    def __init__(self, start_cards=False):
        self.table = Image.open(table_path)  # Открывает фотографию с игровым столом
        self.cards_count = 0

        if start_cards:  # Добавляет карты, если они есть
            [self.add_card(card) for card in start_cards]

    def add_card(self, path_to_card: str) -> bytes:
        """Наносит картинку карты на игровой стол"""
        card = Image.open(path_to_card)
        card = resize_image(card)
        self.table.paste(card, positions[self.cards_count])
        self.cards_count += 1
        return self.get_table()

    def get_table(self) -> bytes:
        """Выдает картинку в байтах"""
        with BytesIO() as output:
            #self.table.save(output, 'JPEG')
            self.table.save(output, 'PNG')
            data = output.getvalue()
        return data
