import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from generate_data import generate_dataset

from neo4j import GraphDatabase


def create_graph_db(num_users=1000, num_stations=50, num_trips=10000,
                     uri="neo4j://localhost:7687", user="neo4j", password="12345678"):
    """
    creates the neo4j graph with nodes and relationships.
    """
    print("=" * 50)
    print("setting up graph database (neo4j)")
    print("=" * 50)
    
    print(f"\ngenerating data: {num_users} users, {num_stations} stations, {num_trips} trips...")
    users, stations, trips, events = generate_dataset(
        num_users=num_users,
        num_stations=num_stations,
        num_trips=num_trips
    )
    print(f"done! also got {len(events)} events")
    
    print(f"\nconnecting to neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        print("clearing old graph...")
        session.run("match (n) detach delete n")
        
        print("creating constraints...")
        session.run("create constraint user_id if not exists for (u:user) require u.user_id is unique")
        session.run("create constraint station_id if not exists for (s:station) require s.station_id is unique")
        session.run("create constraint trip_id if not exists for (t:trip) require t.trip_id is unique")
        
        print("creating user nodes...")
        for u in users:
            session.run("""
                create (u:user {user_id: $user_id, name: $name, 
                               surname: $surname, country: $country})
            """, user_id=u['user_id'], name=u['name'], 
                surname=u['surname'], country=u['country'])
        
        print("creating station nodes...")
        for s in stations:
            session.run("""
                create (s:station {station_id: $station_id, name: $name, 
                                   city: $city, capacity: $capacity})
            """, station_id=s['station_id'], name=s['name'],
                city=s['city'], capacity=s['capacity'])
        
        print("creating trip nodes and relationships...")
        
        users_by_id = {u['user_id']: u for u in users}
        stations_by_id = {s['station_id']: s for s in stations}
        
        for t in trips:
            session.run("""
                match (u:user {user_id: $user_id})
                match (ss:station {station_id: $start_station_id})
                match (es:station {station_id: $end_station_id})
                create (tr:trip {trip_id: $trip_id, start_time: $start_time,
                                  end_time: $end_time, duration: $duration, cost: $cost})
                create (u)-[:made]->(tr)
                create (tr)-[:starts_at]->(ss)
                create (tr)-[:ends_at]->(es)
            """, user_id=t['user_id'], start_station_id=t['start_station_id'],
                end_station_id=t['end_station_id'], trip_id=t['trip_id'],
                start_time=t['start_time'], end_time=t['end_time'],
                duration=t['duration_minutes'], cost=t['cost'])
        
        print("\nsanity checks:")
        result = session.run("match (u:user) return count(u) as count")
        print(f"  user nodes: {result.single()['count']}")
        
        result = session.run("match (s:station) return count(s) as count")
        print(f"  station nodes: {result.single()['count']}")
        
        result = session.run("match (t:trip) return count(t) as count")
        print(f"  trip nodes: {result.single()['count']}")
        
        result = session.run("match ()-[r:made]->() return count(r) as count")
        print(f"  made relationships: {result.single()['count']}")
    
    driver.close()
    print("\nneo4j setup complete.")


if __name__ == "__main__":
    create_graph_db(num_users=100, num_stations=10, num_trips=500)