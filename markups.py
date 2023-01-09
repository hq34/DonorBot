# -*- coding: utf-8 -*-

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
import db


# start menu
btnCreate = KeyboardButton('✍ Ввести данные')
btnAbout = KeyboardButton('📜 Узнать больше')
start_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(btnCreate, btnAbout)

# choosing blood_type menu
btnBlood_1 = KeyboardButton('🅾(I)')
btnBlood_2 = KeyboardButton('🅰(II)')
btnBlood_3 = KeyboardButton('🅱(III)')
btnBlood_4 = KeyboardButton('🆎(IV)')
blood_menu = ReplyKeyboardMarkup(resize_keyboard=True).row(btnBlood_1, btnBlood_2).row(btnBlood_3, btnBlood_4)

# choosing rh-factor menu
btnRhFactor_plus = KeyboardButton('+ Положительный')
btnRhFactor_minus = KeyboardButton('- Отрицательный')
rh_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(btnRhFactor_plus, btnRhFactor_minus)

# send geolocation menu
btnSendLocation = KeyboardButton('🚩 Отправить геолокацию', request_location=True)
location_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(btnSendLocation)

# main menu
btnInfo = KeyboardButton('❓ Инфо')
btnSettings = KeyboardButton('⚙️ Настройки')
main_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(btnSettings, btnInfo)

# info menu
btnBack = KeyboardButton('🔙 Назад')
btnRecommendations = KeyboardButton('🧾 Рекомендации До и После донации')
btnHonorable = KeyboardButton('🏆 Почетный донор')
btnStation = KeyboardButton('🏥 Станция переливания')
info_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(btnRecommendations, btnHonorable, btnStation, btnBack)

# delete menu
btnYes = KeyboardButton('❌ Да')
btnNo = KeyboardButton('✅ Нет')
delete_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(btnYes, btnNo)

# settings menu
btnBack = KeyboardButton('🔙 Назад')
btnDelete = KeyboardButton('❌ Удалить данные')
btnNotifyOff = KeyboardButton('🔕 Отключить уведомления')
btnNotifyOn = KeyboardButton('🔔 Включить уведомления')
settings_menu_notify_off = ReplyKeyboardMarkup(resize_keyboard=True).add(btnNotifyOff, btnDelete, btnBack)
settings_menu_notify_on = ReplyKeyboardMarkup(resize_keyboard=True).add(btnNotifyOn, btnDelete, btnBack)


# stations inline menu
async def make_keyboard_with_nearest_stations(stations):
    buttons = []
    for station_info in stations:
        station_id = station_info[0]
        address = ' '.join(await db.select_address_from_station(station_id=station_id))
        text = f'{address} ({station_info[1]} км)'
        button = InlineKeyboardButton(text, callback_data=station_id)
        buttons.append(button)
    InlineStations = InlineKeyboardMarkup(row_width=1).add(*buttons)
    return InlineStations


