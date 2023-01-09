# -*- coding: utf-8 -*-
import asyncio
import db
from lights_getter import get_lights


async def update_lights_for_stations():
    stations_with_webs = await db.select_websites_from_stations()
    stations_with_lights = await get_lights(stations_with_webs)
    for station_id, lights in stations_with_lights:
        await db.update_lights_to_station(station_id=station_id, lights=lights)


async def update_lights_for_users():  # возможно надо будет переделать перебирая юзеров каждой станции
    users = await db.select_users()
    for user_id in users:
        await update_light_for_one_user(user_id=user_id)


async def update_light_for_one_user(user_id):
    _rh_indices = {'+': 0, '-': 1}
    station_id = await db.select_station_id_from_user(user_id)
    lights = eval((await db.select_lights_from_station(station_id))[0])  # придумать, как сделать без eval()
    blood_type = await db.select_blood_type_from_user(user_id)
    blood, rh = blood_type.split()
    light = lights.get(blood)[_rh_indices.get(rh)]
    await db.update_light_for_user(user_id, light)


async def main():
    await db.db_connect()
    await update_lights_for_stations()


if __name__ == '__main__':
    asyncio.run(main())

