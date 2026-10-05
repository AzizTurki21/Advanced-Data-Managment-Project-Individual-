import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from generate_data import generate_dataset

from pymongo import MongoClient


def create_document_db(num_users=1000, num_stations=50, num_trips=10000, 
                        db_name="mobility_platform"):
    """
    creates mongodb collections and inserts data with embedded documents.
    """
    print("=" * 50)
    print("setting up document database (mongodb)")
    print("=" * 50)
    
    print(f"\ngenerating data: {num_users} users, {num_stations} stations, {num_trips} trips...")
    users, stations, trips, events = generate_dataset(
        num_users=num_users,
        num_stations=num_stations,
        num_trips=num_trips
    )
    print(f"done! also got {len(events)} events")
    
    print("\nconnecting to mongodb at localhost:27017...")
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    
    print("clearing old collections...")
    db.users.drop()
    db.stations.drop()
    db.trips.drop()
    
    print("inserting users...")
    db.users.insert_many(users)
    
    print("inserting stations...")
    db.stations.insert_many(stations)
    
    print("building trip documents with embedded data...")
    
    events_by_trip = {}
    for e in events:
        tid = e['trip_id']
        if tid not in events_by_trip:
            events_by_trip[tid] = []
        event_doc = {
            'event_id': e['event_id'],
            'timestamp': e['timestamp'],
            'type': e['type'],
            'value': e['value']
        }
        events_by_trip[tid].append(event_doc)
    
    users_by_id = {u['user_id']: u for u in users}
    
    trip_docs = []
    for t in trips:
        user = users_by_id[t['user_id']]
        
        trip_doc = {
            'trip_id': t['trip_id'],
            'user': {
                'user_id': user['user_id'],
                'name': user['name'],
                'surname': user['surname'],
                'birthdate': user['birthdate'],
                'country': user['country']
            },
            'start_station_id': t['start_station_id'],
            'end_station_id': t['end_station_id'],
            'start_time': t['start_time'],
            'end_time': t['end_time'],
            'duration_minutes': t['duration_minutes'],
            'cost': t['cost'],
            'events': events_by_trip.get(t['trip_id'], [])
        }
        trip_docs.append(trip_doc)
    
    print(f"inserting {len(trip_docs)} trip documents...")
    db.trips.insert_many(trip_docs)
    
    print(f"\nsanity checks:")
    print(f"  users collection: {db.users.count_documents({})} docs")
    print(f"  stations collection: {db.stations.count_documents({})} docs")
    print(f"  trips collection: {db.trips.count_documents({})} docs")
    
    sample = db.trips.find_one()
    print(f"\nsample trip has {len(sample.get('events', []))} embedded events")
    print(f"sample trip user: {sample['user']['name']} {sample['user']['surname']}")
    
    client.close()
    print("\nmongodb setup complete.")


if __name__ == "__main__":
    create_document_db(num_users=100, num_stations=10, num_trips=500)