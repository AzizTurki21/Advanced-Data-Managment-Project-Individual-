import sqlite3
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from generate_data import generate_dataset


def create_relational_db(num_users=1000, num_stations=50, num_trips=10000, db_path="mobility.db"):
    """
    creates the sqlite database with proper tables and foreign keys.
    returns the connection so we can use it later.
    """
    print("=" * 50)
    print("setting up relational database (sqlite)")
    print("=" * 50)
    
    # generate the fake data
    print(f"\ngenerating data: {num_users} users, {num_stations} stations, {num_trips} trips...")
    users, stations, trips, events = generate_dataset(
        num_users=num_users, 
        num_stations=num_stations, 
        num_trips=num_trips
    )
    print(f"done! also got {len(events)} events")
    

    print(f"\ncreating database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
 
    cursor.execute("pragma foreign_keys = on")
    
  
    cursor.execute("drop table if exists events")
    cursor.execute("drop table if exists trips")
    cursor.execute("drop table if exists stations")
    cursor.execute("drop table if exists users")
    
    cursor.execute("""
        create table users (
            user_id integer primary key,
            name text not null,
            surname text not null,
            birthdate text,
            country text
        )
    """)
    
    cursor.execute("""
        create table stations (
            station_id integer primary key,
            name text not null,
            city text not null,
            capacity integer
        )
    """)
    
    cursor.execute("""
        create table trips (
            trip_id integer primary key,
            user_id integer not null,
            start_station_id integer not null,
            end_station_id integer not null,
            start_time text,
            end_time text,
            duration_minutes integer,
            cost real,
            foreign key (user_id) references users(user_id),
            foreign key (start_station_id) references stations(station_id),
            foreign key (end_station_id) references stations(station_id)
        )
    """)
    
    cursor.execute("""
        create table events (
            event_id integer primary key,
            trip_id integer not null,
            timestamp text,
            type text,
            value text,
            foreign key (trip_id) references trips(trip_id)
        )
    """)
    
    print("tables created: users, stations, trips, events")
    
    
    for u in users:
        cursor.execute("""
            insert into users (user_id, name, surname, birthdate, country)
            values (?, ?, ?, ?, ?)
        """, (u['user_id'], u['name'], u['surname'], u['birthdate'], u['country']))
    
    for s in stations:
        cursor.execute("""
            insert into stations (station_id, name, city, capacity)
            values (?, ?, ?, ?)
        """, (s['station_id'], s['name'], s['city'], s['capacity']))
    
    for t in trips:
        cursor.execute("""
            insert into trips (trip_id, user_id, start_station_id, end_station_id,
                               start_time, end_time, duration_minutes, cost)
            values (?, ?, ?, ?, ?, ?, ?, ?)
        """, (t['trip_id'], t['user_id'], t['start_station_id'], t['end_station_id'],
              t['start_time'], t['end_time'], t['duration_minutes'], t['cost']))
    
    for e in events:
        cursor.execute("""
            insert into events (event_id, trip_id, timestamp, type, value)
            values (?, ?, ?, ?, ?)
        """, (e['event_id'], e['trip_id'], e['timestamp'], e['type'], e['value']))
    
    conn.commit()
    print(f"inserted {len(users)} users, {len(stations)} stations, {len(trips)} trips, {len(events)} events")
    
    cursor.execute("select count(*) from users")
    user_count = cursor.fetchone()[0]
    print(f"\nsanity check: {user_count} users in database")
    
    return conn


if __name__ == "__main__":
    conn = create_relational_db(num_users=100, num_stations=10, num_trips=500)
    conn.close()