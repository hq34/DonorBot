# -*- coding: utf-8 -*-

import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.reply_keyboard import ReplyKeyboardRemove
import aioschedule

from config import telegram_token as token
from config import States
import markups as nav
import answers
import db
import updator as upd
from geolocations import find_nearest_points


bot = Bot(token=token)
dp = Dispatcher(bot)


async def update_lights():
    await upd.update_lights_for_stations()
    await upd.update_lights_for_users()


async def send_light_to_user(user_id):
    light = await db.select_light_from_user(user_id=user_id)
    await bot.send_message(user_id, text=(answers.at_the_moment + answers.blood_notifies.get(light)))


async def send_lights_to_users():
    users_info = await db.select_users_with_lights()
    for user_id, light, notify, station_id in users_info:

        if notify:
            await bot.send_message(user_id, answers.blood_notifies.get(light))
            if light != '-max':
                message = await answers.create_station_info(station_id=station_id)
                await bot.send_message(user_id, message)


async def scheduler():
    aioschedule.every().day.at('10:00').do(update_lights)
    aioschedule.every().day.at('14:00').do(send_lights_to_users)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    await db.db_connect()
    asyncio.create_task(scheduler())


@dp.message_handler(commands=['start'])
async def commend_start(message: types.Message):
    if await db.check_user_for_availability(user_id=message.from_user.id):
        match db.select_user_state(message.from_user.id):
            case States.S_START_MENU:
                await bot.send_message(message.from_user.id, text=answers.greetings, reply_markup=nav.start_menu)
            case States.S_CHOOSE_BLOOD:
                text = f'{answers.not_finished}\n{answers.choice_blood_type}'
                await bot.send_message(message.from_user.id, text=text, reply_markup=nav.blood_menu)
            case States.S_CHOOSE_RH_FACTOR:
                text = f'{answers.not_finished}\n{answers.choice_rh_factor}'
                await bot.send_message(message.from_user.id, text=text, reply_markup=nav.rh_menu)
            case States.S_ENTER_LOCATION:
                text = f'{answers.not_finished}\n{answers.enter_location}'
                await bot.send_message(message.from_user.id, text=text, reply_markup=nav.location_menu)
            case _:
                await db.enable_notifications(user_id=message.from_user.id)
                await bot.send_message(message.from_user.id, text=answers.greetings_again, reply_markup=nav.main_menu)
                await db.update_user_state(user_id=message.from_user.id, state=States.S_MAIN_MENU)

    else:
        await db.add_new_user(user_id=message.from_user.id)
        await bot.send_message(message.from_user.id, text=answers.greetings, reply_markup=nav.start_menu)
        await db.update_user_state(user_id=message.from_user.id, state=States.S_START_MENU)


@dp.message_handler(lambda message: db.select_user_state(message.from_user.id) == States.S_START_MENU)
async def start_menu(message: types.Message):
    match message.text:
        case '📜 Узнать больше':
            await bot.send_message(message.from_user.id, text=answers.about)
        case '✍ Ввести данные':
            await bot.send_message(message.from_user.id, text=answers.choice_blood_type, reply_markup=nav.blood_menu)
            await db.update_user_state(user_id=message.from_user.id, state=States.S_CHOOSE_BLOOD)


@dp.message_handler(lambda message: db.select_user_state(message.from_user.id) == States.S_CHOOSE_BLOOD)
async def choose_blood(message: types.Message):
    if message.text in ('🅾(I)', '🅰(II)', '🅱(III)', '🆎(IV)'):
        await db.write_blood_type_into_users(message.from_user.id, message.text)
        await bot.send_message(message.from_user.id, text=answers.choice_rh_factor, reply_markup=nav.rh_menu)
        await db.update_user_state(user_id=message.from_user.id, state=States.S_CHOOSE_RH_FACTOR)


@dp.message_handler(lambda message: db.select_user_state(message.from_user.id)[0][0] == States.S_CHOOSE_RH_FACTOR)
async def choose_rh_factor(message: types.Message):
    if message.text in ('+ Положительный', '- Отрицательный'):
        await db.write_rh_factor_to_user(user_id=message.from_user.id, rh_factor=message.text)
        await bot.send_message(message.from_user.id, text=answers.enter_location, reply_markup=nav.location_menu)
        await db.update_user_state(user_id=message.from_user.id, state=States.S_ENTER_LOCATION)


@dp.message_handler(lambda message: db.select_user_state(message.from_user.id) in (States.S_ENTER_LOCATION, States.S_CHANGING_STATION),
                    content_types=['location'])
async def enter_location(message: types.Message):
    nearest_stations = await find_nearest_points((message.location.latitude, message.location.longitude))
    inline_keyboard = await nav.make_keyboard_with_nearest_stations(nearest_stations)
    await bot.send_message(message.from_user.id, text=answers.change_station, reply_markup=inline_keyboard)


@dp.callback_query_handler(lambda message: db.select_user_state(message.from_user.id) in (States.S_ENTER_LOCATION, States.S_CHANGING_STATION))
async def change_location(callback: types.CallbackQuery):
    await db.write_user_station(user_id=callback.from_user.id, station_id=callback.data)
    await upd.update_light_for_one_user(user_id=callback.from_user.id)
    match await db.select_user_state(callback.from_user.id):
        case States.S_ENTER_LOCATION:
            await bot.send_message(callback.from_user.id, text=answers.saved_data, reply_markup=nav.main_menu)
        case States.S_CHANGING_STATION:
            await bot.send_message(callback.from_user.id, text=answers.station_changed, reply_markup=nav.main_menu)
    await send_light_to_user(user_id=callback.from_user.id)
    await db.update_user_state(user_id=callback.from_user.id, state=States.S_MAIN_MENU)


@dp.message_handler(lambda message: db.select_user_state(message.from_user.id) == States.S_MAIN_MENU)
async def main_menu(message: types.Message):
    match message.text:
        case '🩸 Проверить наличие':
            await send_light_to_user(message.from_user.id)
        case '⚙️ Настройки':
            if await db.check_notify_from_user(message.from_user.id):
                await bot.send_message(message.from_user.id, text=answers.settings_menu, reply_markup=nav.settings_menu_notify_off)
            else:
                await bot.send_message(message.from_user.id, text=answers.settings_menu, reply_markup=nav.settings_menu_notify_on)
            await db.update_user_state(user_id=message.from_user.id, state=States.S_SETTINGS_MENU)
        case '❓ Инфо':
            await bot.send_message(message.from_user.id, text='Меню инфо', reply_markup=nav.info_menu)
            await db.update_user_state(user_id=message.from_user.id, state=States.S_INFO_MENU)


@dp.message_handler(lambda message: db.select_user_state(message.from_user.id) == States.S_INFO_MENU)
async def info_menu(message: types.Message):
    match message.text:
        case '🧾 Рекомендации До и После донации':
            with open(answers.imgs.get('recommendations'), 'rb') as img_recs:
                await bot.send_photo(message.from_user.id, photo=img_recs, reply_markup=nav.info_menu)
        case '🏆 Почетный донор':
            with open(answers.imgs.get('honorable'), 'rb') as img_honor:
                await bot.send_photo(message.from_user.id, photo=img_honor, reply_markup=nav.info_menu)
        case '🏥 Станция переливания':
            station_id = await db.select_station_id_from_user(message.from_user.id)
            text = await answers.create_station_info(station_id=station_id)
            await bot.send_message(message.from_user.id, text=text, reply_markup=nav.info_menu)
        case '🔙 Назад':
            await bot.send_message(message.from_user.id, text=answers.back_to_main_menu, reply_markup=nav.main_menu)
            await db.update_user_state(user_id=message.from_user.id, state=States.S_MAIN_MENU)


@dp.message_handler(lambda message: db.select_user_state(message.from_user.id) == States.S_SETTINGS_MENU)
async def settings_menu(message: types.Message):
    match message.text:
        case '🏥 Сменить станцию':
            await db.update_user_state(user_id=message.from_user.id, state=States.S_CHANGING_STATION)
            await bot.send_message(message.from_user.id, text=answers.enter_location, reply_markup=nav.location_menu)
        case '🔕 Отключить уведомления':
            await db.disable_notifications(message.from_user.id)
            await bot.send_message(message.from_user.id, text=answers.notification_disabled, reply_markup=nav.settings_menu_notify_on)
        case '🔔 Включить уведомления':
            await db.enable_notifications(message.from_user.id)
            await bot.send_message(message.from_user.id, text=answers.notification_enabled, reply_markup=nav.settings_menu_notify_off)
        case '❌ Удалить данные':
            await bot.send_message(message.from_user.id, text=answers.delete, reply_markup=nav.delete_menu)
            await db.update_user_state(user_id=message.from_user.id, state=States.S_DELETE)
        case '🔙 Назад':
            await bot.send_message(message.from_user.id, text=answers.back_to_main_menu, reply_markup=nav.main_menu)
            await db.update_user_state(user_id=message.from_user.id, state=States.S_MAIN_MENU)


@dp.message_handler(lambda message: db.select_user_state(message.from_user.id) == States.S_DELETE)
async def delete_menu(message: types.Message):
    match message.text:
        case '❌ Да':
            await db.delete_user(message.from_user.id)
            await bot.send_message(message.from_user.id, text=answers.data_deleted, reply_markup=ReplyKeyboardRemove(True))
        case '✅ Нет':
            await bot.send_message(message.from_user.id, text=answers.back_to_main_menu, reply_markup=nav.main_menu)
            await db.update_user_state(user_id=message.from_user.id, state=States.S_MAIN_MENU)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

