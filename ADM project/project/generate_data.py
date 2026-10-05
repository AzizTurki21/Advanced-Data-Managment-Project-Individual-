import random
from datetime import datetime, timedelta

cities = ["rome", "milan", "naples", "turin", "palermo", "genoa", 
          "bologna", "florence", "bari", "catania"]
first_names = ["marco", "giulia", "luca", "sofia", "alessandro", "emma",
               "lorenzo", "giorgia", "andrea", "martina", "matteo", "chiara",
               "davide", "sara", "simone", "alice", "gabriele", "greta",
               "riccardo", "francesca"]
last_names = ["rossi", "ferrari", "bianchi", "romano", "gallo", "costa",
              "fontana", "conti", "esposito", "bruno", "rizzo", "moretti",
              "marino", "ferri", "martini", "greco", "barbieri", "lombardi",
              "giordano", "colombo"]
countries = ["italy", "france", "germany", "spain", "uk", "usa", 
             "netherlands", "belgium", "switzerland", "austria"]


event_types = ["gps", "error", "battery", "delay"]


def generate_dataset(num_users=1000, num_stations=50, num_trips=10000, 
                     events_per_trip_dist=None, seed=None):
   
    if seed is not None:
        random.seed(seed)

    if events_per_trip_dist is None:
    
        events_per_trip_dist = [0.2, 0.3, 0.3, 0.2]

    event_counts = [0, 2, 5, 10]


    users = []
    for i in range(1, num_users + 1):
        birthdate = datetime(1960, 1, 1) + timedelta(days=random.randint(0, 20000))
        users.append({
            'user_id': i,
            'name': random.choice(first_names),
            'surname': random.choice(last_names),
            'birthdate': birthdate.strftime('%Y-%m-%d'),
            'country': random.choice(countries)
        })


    stations = []
    for i in range(1, num_stations + 1):
        city = random.choice(cities)
        stations.append({
            'station_id': i,
            'name': f"station {i} - {city}",
            'city': city,
            'capacity': random.randint(10, 100)
        })


    trips = []
    for i in range(1, num_trips + 1):
        user = random.choice(users)
        start_station = random.choice(stations)
        end_station = random.choice(stations)

      
        while end_station == start_station and random.random() < 0.8:
            end_station = random.choice(stations)

   
        start_time = datetime(2024, 1, 1) + timedelta(
            days=random.randint(0, 365), 
            minutes=random.randint(0, 1439)
        )
     
        duration = random.randint(5, 180)
        end_time = start_time + timedelta(minutes=duration)

        cost = round(duration * random.uniform(0.1, 0.5), 2)

        trips.append({
            'trip_id': i,
            'user_id': user['user_id'],
            'start_station_id': start_station['station_id'],
            'end_station_id': end_station['station_id'],
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_minutes': duration,
            'cost': cost
        })

    # ---------- events ----------
    events = []
    event_id = 1
    for trip in trips:
  
        num_events = random.choices(event_counts, weights=events_per_trip_dist)[0]

        for _ in range(num_events):
  
            event_time = datetime.strptime(trip['start_time'], '%Y-%m-%d %H:%M:%S') \
                         + timedelta(minutes=random.randint(0, trip['duration_minutes']))

            event_type = random.choice(event_types)

            if event_type == "gps":
   
                lat = random.uniform(36.0, 47.0)
                lon = random.uniform(7.0, 19.0)
                value = f"{lat:.4f},{lon:.4f}"
                battery_level = None
            elif event_type == "error":
                value = random.choice(["engine_failure", "tire_puncture", 
                                       "brake_issue", "sensor_malfunction"])
                battery_level = None
            elif event_type == "battery":
                value = str(random.randint(0, 100))
                battery_level = int(value) 
            else:  # delay
                value = str(random.randint(1, 30))
                battery_level = None

            event_doc = {
                'event_id': event_id,
                'trip_id': trip['trip_id'],
                'timestamp': event_time.strftime('%Y-%m-%d %H:%M:%S'),
                'type': event_type,
                'value': value
            }

    
            if battery_level is not None:
                event_doc['battery_level'] = battery_level

            events.append(event_doc)
            event_id += 1

    return users, stations, trips, events


if __name__ == "__main__":
    print("generating test data...")
    u, s, t, e = generate_dataset(num_users=100, num_stations=10, 
                                   num_trips=500, seed=42)
    print(f"done! created:")
    print(f"  - {len(u)} users")
    print(f"  - {len(s)} stations")  
    print(f"  - {len(t)} trips")
    print(f"  - {len(e)} events")


    battery_events = [ev for ev in e if ev['type'] == 'battery']
    if battery_events:
        print(f"\nexample battery event: {battery_events[0]}")
    else:
        print("\nno battery events in this run (random)")