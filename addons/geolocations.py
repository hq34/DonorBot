# -*- coding: utf-8 -*-

import asyncio

import db
from geopy.geocoders import Yandex as Ya
from geopy import distance
from config import yandex_token as token


async def convert_addresses_to_coordinates():

    async def find_coordinates(address):
        geolocator = Ya(api_key=token, user_agent='Donor bot')
        address_info = geolocator.geocode(address, exactly_one=False)
        return address_info[0][1]

    stations = await db.check_stations_with_empty_coordinates()
    for station in stations:
        address = station[1] + ' ' + station[2]
        latitude, longitude = await find_coordinates(address)
        station_id = station[0]
        await db.write_coordinates_to_station(station_id=station_id, latitude=latitude, longitude=longitude)


async def find_nearest_points(user_coordinates):

    async def filter_nearest(stations_with_coordinates):
        _max_distance = 5
        for station in stations_with_coordinates:
            if station[1] < _max_distance:
                yield station

    distance_to_stations = []
    station_coordinates = await db.select_station_coordinates()
    for station_coordinate in station_coordinates:
        station_id = station_coordinate[0]
        coordinate = (station_coordinate[1], station_coordinate[2])
        distance_to_station = round(distance.distance(user_coordinates, coordinate).km, 2)
        distance_to_stations.append((station_id, distance_to_station))
    nearest_stations = [station async for station in filter_nearest(distance_to_stations)]
    distance_to_stations.sort(key=lambda d: d[1])
    return nearest_stations if nearest_stations else [distance_to_stations[0]]


async def main():
    from pathlib import Path, PurePath
    path = PurePath((Path().parent.absolute()).parents[0], 'db/donor.db')
    await db.db_connect(path)
    await convert_addresses_to_coordinates()


if __name__ == '__main__':
    asyncio.run(main())
