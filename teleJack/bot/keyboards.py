from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup
)
from teleJack.orm_db import base

game_keyboard = [
    [
        InlineKeyboardButton(text='Взять', callback_data='take'),
        InlineKeyboardButton(text='Пас', callback_data='skip')
     ]
]
game_markup = InlineKeyboardMarkup(game_keyboard)  # Основная игровая клавиатура

text_keyboard = [
    [
        InlineKeyboardButton(text='Новая игра', callback_data='new_text')
    ]
]
text_game_markup = InlineKeyboardMarkup(text_keyboard)  # Клавиатура для новой игры в текстовом режиме

img_keyboard = [
    [
        InlineKeyboardButton(text='Новая игра', callback_data='new_img')
    ]
]
img_game_markup = InlineKeyboardMarkup(img_keyboard)  # Клавиатура для новой игры в графическом режиме

game_type_keyboard = [
    [
        InlineKeyboardButton(text='Текст', callback_data='new_text'),
        InlineKeyboardButton(text='Картинки', callback_data='new_img')
    ]
]
game_type_markup = InlineKeyboardMarkup(game_type_keyboard)

data = [(base.decks[i]['name'], i) for i in base.decks]
shop_start_keyboard = [
    [InlineKeyboardButton(text=j, callback_data=f'show_{k}') for j, k in data[i: i + 3]] for i in range(0, len(data), 3)
]
shop_start_markup = InlineKeyboardMarkup(shop_start_keyboard)
