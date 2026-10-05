import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from generate_data import generate_dataset

from pymongo import MongoClient
import pandas as pd


def get_db(db_name="mobility_platform"):
    """helper to connect and return db, create if empty"""
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    
    if db.trips.count_documents({}) == 0:
        print("collections empty, creating them...")
        from schema import create_document_db
        create_document_db(db_name=db_name)
    
    return client, db


def query1_trips_with_info(db_name="mobility_platform", limit=10):
    """
    query 1: trips with user info and station names.
    
    user info is already embedded, but we need to look up station names
    since i kept stations as a separate collection.
    """
    print("=" * 50)
    print("query 1 (document): trips with user info and station names")
    print("=" * 50)
    
    client, db = get_db(db_name)
    
    stations = {s['station_id']: s['name'] for s in db.stations.find()}
    
    print("\nrunning query...")
    results = []
    
    for trip in db.trips.find().limit(limit):
        results.append({
            'trip_id': trip['trip_id'],
            'user_name': trip['user']['name'],
            'user_surname': trip['user']['surname'],
            'country': trip['user']['country'],
            'start_station': stations.get(trip['start_station_id'], 'unknown'),
            'end_station': stations.get(trip['end_station_id'], 'unknown'),
            'start_time': trip['start_time'],
            'end_time': trip['end_time'],
            'duration_minutes': trip['duration_minutes'],
            'cost': trip['cost']
        })
    
    df = pd.DataFrame(results)
    print(f"showing first {len(df)} results:")
    print(df.to_string())
    
    client.close()
    return df


def query2_user_trip_stats(db_name="mobility_platform", limit=15):
    """
    query 2: users with trip count and average duration.
    
    since trips embed user info, we can group directly on trips.
    but we also need to find users with 0 trips, so we start from 
    the users collection and do a $lookup into trips.
    """
    print("\n" + "=" * 50)
    print("query 2 (document): users with trip count and avg duration")
    print("=" * 50)
    
    client, db = get_db(db_name)
    
    print("\nrunning aggregation pipeline...")

    pipeline = [
        {
            '$lookup': {
                'from': 'trips',
                'localField': 'user_id',
                'foreignField': 'user.user_id',
                'as': 'user_trips'
            }
        },
        {
            '$project': {
                'user_id': 1,
                'name': 1,
                'surname': 1,
                'country': 1,
                'trip_count': {'$size': '$user_trips'},
                'avg_duration': {
                    '$cond': {
                        'if': {'$gt': [{'$size': '$user_trips'}, 0]},
                        'then': {'$avg': '$user_trips.duration_minutes'},
                        'else': 0
                    }
                }
            }
        },
        {'$sort': {'trip_count': -1}},
        {'$limit': limit}
    ]
    
    results = list(db.users.aggregate(pipeline))
    

    formatted = []
    for r in results:
        formatted.append({
            'user_id': r['user_id'],
            'name': r['name'],
            'surname': r['surname'],
            'country': r['country'],
            'trip_count': r['trip_count'],
            'avg_duration': round(r['avg_duration'], 2) if r['avg_duration'] else 0
        })
    
    df = pd.DataFrame(formatted)
    print(f"showing first {len(df)} results:")
    print(df.to_string())
    
    client.close()
    return df


def query3_station_trip_counts(db_name="mobility_platform", limit=15):
    """
    query 3: stations with number of trips started and ended there.
    
    i used the aggregation pipeline to count trips by start_station_id
    and end_station_id, then merge the results.
    """
    print("\n" + "=" * 50)
    print("query 3 (document): stations with trip counts")
    print("=" * 50)
    
    client, db = get_db(db_name)
    
    print("\nrunning aggregation pipeline...")
    
   
    started_pipeline = [
        {'$group': {
            '_id': '$start_station_id',
            'trips_started': {'$sum': 1}
        }}
    ]
    started = {r['_id']: r['trips_started'] for r in db.trips.aggregate(started_pipeline)}
    

    ended_pipeline = [
        {'$group': {
            '_id': '$end_station_id',
            'trips_ended': {'$sum': 1}
        }}
    ]
    ended = {r['_id']: r['trips_ended'] for r in db.trips.aggregate(ended_pipeline)}
    

    results = []
    for station in db.stations.find().limit(limit):
        sid = station['station_id']
        results.append({
            'station_id': sid,
            'name': station['name'],
            'city': station['city'],
            'capacity': station['capacity'],
            'trips_started': started.get(sid, 0),
            'trips_ended': ended.get(sid, 0)
        })
    

    results.sort(key=lambda x: x['trips_started'], reverse=True)
    
    df = pd.DataFrame(results)
    print(f"showing first {len(df)} results:")
    print(df.to_string())
    
    client.close()
    return df


def query4_trips_with_errors(db_name="mobility_platform", limit=10):
    """
    query 4: trips that have at least one error event.
    
    since events are embedded in trips, we just filter trips where 
    at least one event has type 'error'.
    """
    print("\n" + "=" * 50)
    print("query 4 (document): trips with error events")
    print("=" * 50)
    
    client, db = get_db(db_name)
    

    stations = {s['station_id']: s['name'] for s in db.stations.find()}
    
    print("\nrunning query...")
    

    results = []
    for trip in db.trips.find({'events.type': 'error'}).limit(limit):
        results.append({
            'trip_id': trip['trip_id'],
            'user_name': trip['user']['name'],
            'user_surname': trip['user']['surname'],
            'start_station': stations.get(trip['start_station_id'], 'unknown'),
            'end_station': stations.get(trip['end_station_id'], 'unknown'),
            'start_time': trip['start_time'],
            'duration_minutes': trip['duration_minutes'],
            'cost': trip['cost'],
            'error_count': sum(1 for e in trip.get('events', []) if e['type'] == 'error')
        })
    
    df = pd.DataFrame(results)
    print(f"showing first {len(df)} results:")
    print(df.to_string())
    
    client.close()
    return df


if __name__ == "__main__":
    query1_trips_with_info()
    query2_user_trip_stats()
    query3_station_trip_counts()
    query4_trips_with_errors()