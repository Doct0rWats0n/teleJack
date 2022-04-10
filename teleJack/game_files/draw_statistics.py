from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


def draw_statistics(stat: dict, photo: bytes, player_name: str = 'Anonymous') -> bytes:
    """Рисование изображения со статистикой игрового профиля"""
    max_len = get_max_strings_len(stat)
    formatted_strings = get_formatted_strings(stat, max_len)

    img = Image.open('teleJack/static/imgs/stat_good.jpg')
    img2 = Image.open(photo)
    new_img = ImageDraw.Draw(img)
    x, y = 50, 110
    start_position = 500
    font = ImageFont.truetype('teleJack/static/fonts/font.ttf', y)
    line_width, line_space = 8, 12
    line_length = max_len * (y / 1.618)

    img2 = img2.resize((y * 3, y * 3))
    img.paste(img2, (x, start_position // 5))  # Наносит картинку профиля игрока
    new_img.text((x + y * 4, start_position // 5), player_name, font=font, fill=(0, 0, 0))  # Наносит имя пользователя
    # Нанесение строк со статистикой на картинку
    for index, value in enumerate(formatted_strings, start=0):
        new_img.text((x, (start_position + y * index + (line_space * (index - 1)) - line_width)),
                     value, font=font, fill=(0, 0, 0))
        new_img.line(((x, start_position + y * (index + 1) + (line_space * index),
                       (line_length, start_position + y * (index + 1) + (line_space * index)))),
                     fill=(0, 0, 0), width=line_width)
    # Перевод получившейся картинки в байты
    with BytesIO() as output:
        img.save(output, 'JPEG')
        data = output.getvalue()
    return data


def get_max_strings_len(strings: dict) -> int:
    """Получение максимальной длины строки в словаре"""
    string_lens = map(len, [': '.join(map(str, i)) for i in strings.items()])
    max_len = max(string_lens)
    return max_len


def get_formatted_strings(strings: dict, format_len: int) -> list:
    """Форматирование строк под определенную длину"""
    optimal_strings = []
    for name, value in strings.items():
        string = f'{name}: ' + str(value).rjust(format_len - len(name) - 2, ' ')
        optimal_strings.append(string)
    return optimal_strings
