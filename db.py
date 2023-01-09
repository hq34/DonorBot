import asyncio
import sqlite3 as sl

"""
donor.db
users: id:int, user_id:str, station_id:int (foreign_key), blood_type:str, notify:int(1 or 0), light:str, state:int
stations: station_id:int, city_name:str, address:str, phone:str, website:str, lights:str, latitude:str, longitude:str
"""

__database = 'db/donor.db'


async def rewrite_blood_type(bl_type):
    correct_bl_types = {'🅾': '0',
                        '🅰': 'A',
                        '🅱': 'B',
                        '🆎': 'AB',
                        }

    group = bl_type[0]
    result = bl_type.replace(group, correct_bl_types.get(group))
    return result


async def rewrite_rh_factor(rh_factor):
    return rh_factor[0]


async def db_connect():
    global con, cur
    con = sl.connect(__database)
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS stations'
                '(station_id INT PRIMARY KEY,'
                'city_name TEXT,'
                'address TEXT,'
                'phone TEXT,'
                'website TEXT,'
                'lights TEXT,'
                'latitude TEXT,'
                'longitude TEXT);')
    cur.execute('CREATE TABLE IF NOT EXISTS users'
                '(id INT PRIMARY KEY,'
                'user_id TEXT,'
                'station_id INT,'
                'blood_type TEXT,'
                'notify INT,'
                'light TEXT,'
                'state INT,'
                'FOREIGN KEY(station_id) REFERENCES stations(station_id));')
    con.commit()


""" interaction with the USERS table """


async def add_new_user(user_id):
    cur.execute(f'INSERT INTO users VALUES (NULL, "{user_id}", NULL, NULL, 1, NULL, NULL);')
    con.commit()


async def write_blood_type_into_users(user_id, blood_type):
    true_blood_type = await rewrite_blood_type(blood_type)
    cur.execute(f"UPDATE users SET blood_type='{true_blood_type}' WHERE user_id='{user_id}';")
    con.commit()


async def write_rh_factor_to_user(user_id, rh_factor):
    true_rh_factor = await rewrite_rh_factor(rh_factor)
    cur.execute(f"UPDATE users SET blood_type=(blood_type || ' {true_rh_factor}') WHERE user_id='{user_id}';")
    con.commit()


async def write_user_station(user_id, station_id):
    cur.execute(f'UPDATE users SET station_id={station_id} WHERE user_id="{user_id}";')
    con.commit()


async def disable_notifications(user_id):
    cur.execute(f"UPDATE users SET notify=0 WHERE user_id='{user_id}';")
    con.commit()


async def enable_notifications(user_id):
    cur.execute(f"UPDATE users SET notify=1 WHERE user_id='{user_id}';")
    con.commit()


async def delete_user(user_id):
    cur.execute(f"DELETE FROM users WHERE user_id='{user_id}';")
    con.commit()


async def select_users_blood_type_from_station(station_id):
    return cur.execute(f'SELECT user_id, blood_type FROM users WHERE station_id={station_id};').fetchall()


async def update_light_for_user(user_id, light):
    cur.execute(f'UPDATE users SET light="{light}" WHERE user_id="{user_id}";')
    con.commit()


async def select_users_with_lights():
    return cur.execute('SELECT user_id, light, notify, station_id FROM users').fetchall()


async def select_station_id_from_user(user_id):
    return cur.execute(f'SELECT station_id FROM users WHERE user_id="{user_id}";').fetchone()[0]


async def select_blood_type_from_user(user_id):
    return cur.execute(f'SELECT blood_type FROM users WHERE user_id="{user_id}";').fetchone()[0]


async def check_user_for_availability(user_id):
    return cur.execute(f'SELECT * FROM users WHERE user_id="{user_id}";').fetchone()


async def check_notify_from_user(user_id):
    return cur.execute(f'SELECT notify FROM users WHERE user_id="{user_id}";').fetchone()[0]


async def update_user_state(user_id, state):
    cur.execute(f'UPDATE users set state="{state}" WHERE user_id="{user_id}"')
    con.commit()


def select_user_state(user_id):
    return cur.execute(f'SELECT state FROM users WHERE user_id="{user_id}";').fetchone()[0]


async def select_users():
    return cur.execute('SELECT user_id FROM users;').fetchone()


async def select_light_from_user(user_id):
    return cur.execute(f'SELECT light FROM users WHERE user_id="{user_id}";').fetchone()[0]


async def clear_blood_from_user(user_id):
    cur.execute(f'UPDATE users SET blood_type=NULL WHERE user_id="{user_id}";')
    con.commit()

""" interaction with the STATIONS table """


async def add_new_station(city_name, address, phone, url):
    cur.execute(f'INSERT INTO stations VALUES (NULL, "{city_name}", "{address}", "{phone}", "{url}", NULL, NULL, NULL);')
    con.commit()


async def update_lights_to_station(station_id, lights):
    cur.execute(f'UPDATE stations SET lights="{lights}" WHERE station_id={station_id};')
    con.commit()


async def select_websites_from_stations():
    return cur.execute("SELECT station_id, website FROM stations;").fetchall()


async def select_websites_from_stations_with_empty_lights():
    return cur.execute("SELECT station_id, website FROM stations WHERE lights='{}';").fetchall()


async def select_lights_from_station(station_id):
    return cur.execute(f'SELECT lights FROM stations WHERE station_id="{station_id}";').fetchone()


async def select_address_from_station(station_id):
    return cur.execute(f'SELECT city_name, address FROM stations WHERE station_id="{station_id}";').fetchone()


async def select_phone_and_address_from_station(station_id):
    return cur.execute(f'SELECT phone, city_name, address FROM stations WHERE station_id="{station_id}";').fetchone()


async def check_stations_with_empty_coordinates():
    return cur.execute('SELECT station_id, city_name, address FROM stations '
                       'WHERE longitude is NULL OR latitude is NULL;').fetchall()


async def write_coordinates_to_station(station_id, latitude, longitude):
    cur.execute(f'UPDATE stations SET latitude={latitude}, longitude={longitude} '
                f'WHERE station_id={station_id};')
    con.commit()


async def select_station_coordinates():
    return cur.execute('SELECT station_id, latitude, longitude FROM stations;').fetchall()


async def main():
    await db_connect()


if __name__ == '__main__':
    asyncio.run(main())
