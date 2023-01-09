# -*- coding: utf-8 -*-
import asyncio
import nest_asyncio
import aiohttp
import re
from bs4 import BeautifulSoup

from config import user_agent


async def parser(station_id, html):

    def rewrite_light(light):
        return '-' if light == '-gray' else light

    html_doc = BeautifulSoup(html, features='html.parser')
    tag_lights = html_doc.find_all('div', class_='spk-lights__group-item')
    rh_factors = html_doc.find_all('div', class_='spk-lights__head')
    rh_factors = list(map(lambda rh_factor: rh_factor.text.strip().replace(' ', ''), rh_factors))
    lights = [(re.split(r'item-', tag_light['class'][1])[1]) for tag_light in tag_lights]
    lights = list(map(rewrite_light, lights))
    result = {rh_factors[i]: (lights[i * 2], lights[i * 2 + 1]) for i in range(len(rh_factors))}
    stations_with_lights.append((station_id, result))


async def fetch(session, url):
    async with session.get(url, headers=user_agent) as response:
        return await response.text()


async def download(station_id, url):
    async with limit:
        async with aiohttp.ClientSession() as session:
            html = await fetch(session, url)
            await parser(station_id, html)


async def get_lights(stations):
    global stations_with_lights, limit
    limit = asyncio.Semaphore(40)
    stations_with_lights = []

    nest_asyncio.apply()
    loop = asyncio.new_event_loop()
    tasks = [loop.create_task(download(*data)) for data in stations]
    tasks = asyncio.gather(*tasks)
    loop.run_until_complete(tasks)
    return stations_with_lights
