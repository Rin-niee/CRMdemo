from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

btn_my_requests = KeyboardButton("Мои заявки")
btn_decline = KeyboardButton("Отказаться от заявок")
btn_open_requests = KeyboardButton("Открытые заявки")

main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(btn_my_requests, btn_decline, btn_open_requests)