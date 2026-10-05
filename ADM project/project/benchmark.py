import time
import sqlite3
from pymongo import MongoClient
import pandas as pd


def benchmark_relational(db_path="pt1_relational/mobility.db", iterations=5):
    """run query 2 on sqlite multiple times"""
    print("=" * 50)
    print("benchmarking relational (sqlite)")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    
    query = """
        select u.name, u.surname, count(t.trip_id) as trip_count
        from users u
        left join trips t on u.user_id = t.user_id
        group by u.user_id
        order by trip_count desc
        limit 100
    """
    
    times = []
    for i in range(iterations):
        start = time.time()
        pd.read_sql(query, conn)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  run {i+1}: {elapsed:.4f}s")
    
    avg = sum(times) / len(times)
    print(f"\naverage: {avg:.4f}s")
    
    conn.close()
    return avg


def benchmark_document(db_name="mobility_platform", iterations=5):
    """run similar query on mongodb"""
    print("\n" + "=" * 50)
    print("benchmarking document (mongodb)")
    print("=" * 50)
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    
    pipeline = [
        {'$lookup': {
            'from': 'trips',
            'localField': 'user_id',
            'foreignField': 'user.user_id',
            'as': 'trips'
        }},
        {'$project': {
            'name': 1,
            'surname': 1,
            'trip_count': {'$size': '$trips'}
        }},
        {'$sort': {'trip_count': -1}},
        {'$limit': 100}
    ]
    
    times = []
    for i in range(iterations):
        start = time.time()
        list(db.users.aggregate(pipeline))
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  run {i+1}: {elapsed:.4f}s")
    
    avg = sum(times) / len(times)
    print(f"\naverage: {avg:.4f}s")
    
    client.close()
    return avg


if __name__ == "__main__":
    print("running benchmarks...\n")
    
    rel_avg = benchmark_relational()
    doc_avg = benchmark_document()
    
    print("\n" + "=" * 50)
    print("summary")
    print("=" * 50)
    print(f"sqlite avg: {rel_avg:.4f}s")
    print(f"mongodb avg: {doc_avg:.4f}s")
    
    if rel_avg < doc_avg:
        print(f"\nsqlite was {doc_avg/rel_avg:.2f}x faster")
    else:
        print(f"\nmongodb was {rel_avg/doc_avg:.2f}x faster")
    
    print("\nnote: on small data the difference is tiny.")
    print("mongodb would win on bigger data because it scales better.")