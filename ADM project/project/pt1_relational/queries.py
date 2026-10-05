import sqlite3
import os
import pandas as pd


def get_connection(db_path="mobility.db"):
    """helper to connect to the database, create if missing"""
    if not os.path.exists(db_path):
        print("database not found, creating it...")
        from schema import create_relational_db
        conn = create_relational_db(db_path=db_path)
    else:
        conn = sqlite3.connect(db_path)
    return conn


def query1_trips_with_info(db_path="mobility.db", limit=10):
    """
    query 1: return all trips with user info and start/end station names.
    
    this needs joins with users and stations (twice — start and end).
    """
    print("=" * 50)
    print("query 1: trips with user info and station names")
    print("=" * 50)
    
    conn = get_connection(db_path)
    
    query = """
        select 
            t.trip_id,
            u.name as user_name,
            u.surname as user_surname,
            u.country,
            ss.name as start_station,
            es.name as end_station,
            t.start_time,
            t.end_time,
            t.duration_minutes,
            t.cost
        from trips t
        join users u on t.user_id = u.user_id
        join stations ss on t.start_station_id = ss.station_id
        join stations es on t.end_station_id = es.station_id
        limit ?
    """
    
    print("\nrunning query...")
    df = pd.read_sql(query, conn, params=(limit,))
    print(f"showing first {len(df)} results:")
    print(df.to_string())
    
    conn.close()
    return df


def query2_user_trip_stats(db_path="mobility.db", limit=15):
    """
    query 2: return all users with number of trips and average duration.
    
    this uses group by with count and avg. i used left join so we 
    also see users with 0 trips.
    """
    print("\n" + "=" * 50)
    print("query 2: users with trip count and avg duration")
    print("=" * 50)
    
    conn = get_connection(db_path)
    
    query = """
        select 
            u.user_id,
            u.name,
            u.surname,
            u.country,
            count(t.trip_id) as trip_count,
            coalesce(avg(t.duration_minutes), 0) as avg_duration
        from users u
        left join trips t on u.user_id = t.user_id
        group by u.user_id, u.name, u.surname, u.country
        order by trip_count desc
        limit ?
    """
    
    print("\nrunning query...")
    df = pd.read_sql(query, conn, params=(limit,))
    print(f"showing first {len(df)} results:")
    print(df.to_string())
    
    conn.close()
    return df


def query3_station_trip_counts(db_path="mobility.db", limit=15):
    """
    query 3: return stations with number of trips started and ended there.
    
    i count both start and end trips for each station to see 
    which stations are most popular.
    """
    print("\n" + "=" * 50)
    print("query 3: stations with trip counts")
    print("=" * 50)
    
    conn = get_connection(db_path)
    
    query = """
        select 
            s.station_id,
            s.name,
            s.city,
            s.capacity,
            count(distinct t_start.trip_id) as trips_started,
            count(distinct t_end.trip_id) as trips_ended
        from stations s
        left join trips t_start on s.station_id = t_start.start_station_id
        left join trips t_end on s.station_id = t_end.end_station_id
        group by s.station_id, s.name, s.city, s.capacity
        order by trips_started desc
        limit ?
    """
    
    print("\nrunning query...")
    df = pd.read_sql(query, conn, params=(limit,))
    print(f"showing first {len(df)} results:")
    print(df.to_string())
    
    conn.close()
    return df


def query4_trips_with_errors(db_path="mobility.db", limit=10):
    """
    query 4: return trips that have at least one error event.
    
    this joins trips with events and filters for error type.
    """
    print("\n" + "=" * 50)
    print("query 4: trips with error events")
    print("=" * 50)
    
    conn = get_connection(db_path)
    
    query = """
        select distinct
            t.trip_id,
            u.name as user_name,
            u.surname as user_surname,
            ss.name as start_station,
            es.name as end_station,
            t.start_time,
            t.duration_minutes,
            t.cost
        from trips t
        join users u on t.user_id = u.user_id
        join stations ss on t.start_station_id = ss.station_id
        join stations es on t.end_station_id = es.station_id
        join events e on t.trip_id = e.trip_id
        where e.type = 'error'
        limit ?
    """
    
    print("\nrunning query...")
    df = pd.read_sql(query, conn, params=(limit,))
    print(f"showing first {len(df)} results:")
    print(df.to_string())
    
    conn.close()
    return df


if __name__ == "__main__":
    query1_trips_with_info()
    query2_user_trip_stats()
    query3_station_trip_counts()
    query4_trips_with_errors()