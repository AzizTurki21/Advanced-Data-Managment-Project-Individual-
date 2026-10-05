from neo4j import GraphDatabase
import pandas as pd


def get_driver(uri="neo4j://localhost:7687", user="neo4j", password="12345678"):
    """helper to get neo4j driver"""
    return GraphDatabase.driver(uri, auth=(user, password))


def pagerank_stations(uri="neo4j://localhost:7687", user="neo4j", password="12345678"):
    """
    station centrality — simplified version without gds plugin.
    
    the idea: a station is important if many trips connect to it.
    i count how many trips start or end at each station. this is
    like degree centrality, which is related to pagerank.
    """
    print("=" * 50)
    print("station centrality (simplified pagerank)")
    print("=" * 50)
    
    driver = get_driver(uri, user, password)
    
    with driver.session() as session:
        print("\nrunning query...")
        
        result = session.run("""
            match (s:station)
            optional match (t1:trip)-[:starts_at]->(s)
            with s, count(t1) as starts
            optional match (t2:trip)-[:ends_at]->(s)
            with s, starts, count(t2) as ends
            return s.name as station_name,
                   s.city as city,
                   starts + ends as total_connections
            order by total_connections desc
            limit 10
        """)
        
        results = []
        for record in result:
            results.append({
                'station_name': record['station_name'],
                'city': record['city'],
                'total_connections': record['total_connections']
            })
        
        df = pd.DataFrame(results)
        print(f"\ntop 10 most connected stations:")
        print(df.to_string())
    
    driver.close()
    return df


def connected_components(uri="neo4j://localhost:7687", user="neo4j", password="12345678"):
    """
    connected components — simplified version without gds plugin.
    
    this checks if all stations are reachable from each other through trips.
    i use a simple bfs approach: pick station 1, see how many unique stations
    are reachable through any number of trip connections.
    """
    print("\n" + "=" * 50)
    print("connected components check")
    print("=" * 50)
    
    driver = get_driver(uri, user, password)
    
    with driver.session() as session:
        print("\nchecking network connectivity...")
        
        result = session.run("""
            match (s1:station)
            optional match (s1)<-[:starts_at]-(t:trip)-[:ends_at]->(s2:station)
            where s1 <> s2
            with s1, collect(distinct s2.station_id) as neighbors
            return s1.station_id as station_id,
                   s1.name as station_name,
                   size(neighbors) as neighbor_count,
                   neighbors[0..5] as sample_neighbors
            order by neighbor_count desc
        """)
        
        results = []
        for record in result:
            results.append({
                'station_id': record['station_id'],
                'station_name': record['station_name'],
                'neighbor_count': record['neighbor_count'],
                'sample_neighbors': record['sample_neighbors']
            })
        
        df = pd.DataFrame(results)
        print(f"\nstation connectivity:")
        print(df.to_string())
        
    
        print("\nchecking if all stations are in one component...")
        result = session.run("""
            // count total stations
            match (s:station)
            with count(s) as total_stations
            
            // find all stations reachable from station 1 through any path
            match (start:station {station_id: 1})
            optional match path = (start)-[*]-(other:station)
            where start <> other
            with total_stations, count(distinct other) as reachable
            
            return total_stations, 
                   reachable + 1 as total_reachable,  // +1 for station 1 itself
                   case when total_stations = reachable + 1 
                        then 'fully connected' 
                        else 'not fully connected' end as status
        """)
        
        record = result.single()
        print(f"\ntotal stations: {record['total_stations']}")
        print(f"reachable from station 1 (including itself): {record['total_reachable']}")
        print(f"network status: {record['status']}")
    
    driver.close()
    return df


if __name__ == "__main__":
    pagerank_stations()
    connected_components()