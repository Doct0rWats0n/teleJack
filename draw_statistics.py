from PIL import Image, ImageDraw, ImageFont
from orm_db import base_control
from orm_db.data import db_session
db_session.global_init('orm_db/db/user_base.sqlite')
base = base_control.Controller()


def draw_statistics(player_id: int, player_name: str = 'Anonymous'):
    """Отрисовать статистику игрока"""
    statistics = base.get_player_statistics(player_id)
    max_len = get_max_strings_len(statistics)
    formatted_strings = get_formatted_strings(statistics, max_len)

    img = Image.open('static/imgs/stat_good.jpg')
    new_img = ImageDraw.Draw(img)
    x, y = 50, 100
    start_position = 500
    font = ImageFont.truetype('static/fonts/font.ttf', y)
    line_width, line_space = 8, 12
    line_length = max_len * (y / 1.618)

    new_img.text((x, start_position // 5), player_name, font=font, fill=(0, 0, 0))

    for index, value in enumerate(formatted_strings, start=0):
        new_img.text((x, (start_position + y * index + (line_space * (index - 1)) - line_width)),
                     value, font=font, fill=(0, 0, 0))
        new_img.line(((x, start_position + y * (index + 1) + (line_space * index),
                       (line_length, start_position + y * (index + 1) + (line_space * index)))),
                     fill=(0, 0, 0), width=line_width)
    img.save('test.jpg')


def get_max_strings_len(strings: dict):
    """Возвращает максимальную длину строки в словаре"""
    string_lens = map(len, [': '.join(map(str, i)) for i in strings.items()])
    max_len = max(string_lens)
    return max_len


def get_formatted_strings(strings: dict, format_len: int):
    """Отформатировать все строки под определенный размер"""
    optimal_strings = []
    for name, value in strings.items():
        string = f'{name}: ' + str(value).rjust(format_len - len(name) - 2, ' ')
        optimal_strings.append(string)
    return optimal_strings


draw_statistics(1)
