import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from generate_data import generate_dataset

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, lit, when


def spark_station_popularity(db_name="mobility_platform"):
    """
    station popularity using spark sql.
    
    this is like pagerank but simpler: count how many trips start
    or end at each station. more connections = more important station.
    """
    print("=" * 50)
    print("spark station popularity")
    print("=" * 50)
    
    spark = SparkSession.builder \
        .appName("mobility_popularity") \
        .getOrCreate()
    
    print("\ngenerating local data...")
    users, stations, trips, events = generate_dataset(num_users=100, num_stations=10, num_trips=500)
    
    stations_df = spark.createDataFrame(stations)
    trips_df = spark.createDataFrame(trips)
    
    starts = trips_df.groupBy("start_station_id") \
        .agg(count("*").alias("trips_started"))
    
    ends = trips_df.groupBy("end_station_id") \
        .agg(count("*").alias("trips_ended"))
    
    result = stations_df \
        .join(starts, stations_df["station_id"] == starts["start_station_id"], "left") \
        .join(ends, stations_df["station_id"] == ends["end_station_id"], "left") \
        .select(
            stations_df["station_id"],
            stations_df["name"],
            stations_df["city"],
            coalesce(starts["trips_started"], lit(0)).alias("trips_started"),
            coalesce(ends["trips_ended"], lit(0)).alias("trips_ended")
        ) \
        .withColumn("total_connections", col("trips_started") + col("trips_ended")) \
        .orderBy(col("total_connections").desc())
    
    print("\ntop stations by popularity:")
    result.show(10, truncate=False)
    
    spark.stop()
    print("\ndone.")


def spark_connectivity_check(db_name="mobility_platform"):
    """
    check network connectivity using spark sql.
    
    this finds which stations are connected by direct trips.
    if every station appears in at least one trip, the network is connected.
    """
    print("\n" + "=" * 50)
    print("spark connectivity check")
    print("=" * 50)
    
    spark = SparkSession.builder \
        .appName("mobility_connectivity") \
        .getOrCreate()
    
    print("\ngenerating local data...")
    users, stations, trips, events = generate_dataset(num_users=100, num_stations=10, num_trips=500)
    
    trips_df = spark.createDataFrame(trips)
    stations_df = spark.createDataFrame(stations)
    
    start_stations = trips_df.select(col("start_station_id").alias("station_id")).distinct()
    end_stations = trips_df.select(col("end_station_id").alias("station_id")).distinct()
    connected = start_stations.union(end_stations).distinct()
    
    total = stations_df.count()
    connected_count = connected.count()
    
    print(f"\ntotal stations: {total}")
    print(f"stations in trips: {connected_count}")
    
    isolated = stations_df.join(connected, "station_id", "left_anti")
    
    print(f"\nisolated stations (not in any trip):")
    isolated.show(truncate=False)
    
    spark.stop()
    print("\ndone.")


from pyspark.sql.functions import coalesce


if __name__ == "__main__":
    spark_station_popularity()
    spark_connectivity_check()