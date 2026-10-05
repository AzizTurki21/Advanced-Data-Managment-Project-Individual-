import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from generate_data import generate_dataset

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg, coalesce, lit


def spark_query2(db_name="mobility_platform"):
    """
    spark implementation of query 2 on mongodb data.
    
    reads trips from mongodb, groups by user, computes count and avg.
    then joins with users to include users with 0 trips.
    """
    print("=" * 50)
    print("spark query 2: users with trip count and avg duration")
    print("=" * 50)
    
    jar_path = "mongo-spark-connector_2.12-10.2.2.jar"
    
    if not os.path.exists(jar_path):
        print(f"\nwarning: {jar_path} not found!")
        print("falling back to local data generation instead of mongodb read.")
        print("to use mongodb, download the jar from:")
        print("https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/10.2.2/")
        run_without_mongodb()
        return
    
    print("\nstarting spark session with mongo connector...")
    spark = SparkSession.builder \
        .appName("mobility_query2") \
        .config("spark.jars", jar_path) \
        .config("spark.mongodb.input.uri", f"mongodb://localhost:27017/{db_name}.trips") \
        .config("spark.mongodb.output.uri", f"mongodb://localhost:27017/{db_name}.trips") \
        .getOrCreate()
    
    print("reading trips from mongodb...")
    trips_df = spark.read \
        .format("mongo") \
        .option("uri", f"mongodb://localhost:27017/{db_name}.trips") \
        .load()
    
    users_df = spark.read \
        .format("mongo") \
        .option("uri", f"mongodb://localhost:27017/{db_name}.users") \
        .load()
    
    print(f"loaded {trips_df.count()} trips and {users_df.count()} users")
    
    print("\ncomputing trip stats per user...")
    trip_stats = trips_df.groupBy("user.user_id") \
        .agg(
            count("*").alias("trip_count"),
            avg("duration_minutes").alias("avg_duration")
        )
    
    print("joining with users...")
    result = users_df.join(
        trip_stats,
        users_df["user_id"] == trip_stats["user.user_id"],
        "left_outer"
    ).select(
        users_df["user_id"],
        users_df["name"],
        users_df["surname"],
        users_df["country"],
        coalesce(trip_stats["trip_count"], lit(0)).alias("trip_count"),
        coalesce(trip_stats["avg_duration"], lit(0)).alias("avg_duration")
    ).orderBy(col("trip_count").desc())
    
    print("\nresults:")
    result.show(15, truncate=False)
    
    spark.stop()
    print("\nspark session stopped.")


def run_without_mongodb():
    """
    fallback: generate data locally and use spark on it.
    this proves the spark logic works even without the mongo connector.
    """
    print("\n" + "=" * 50)
    print("fallback mode: using local data")
    print("=" * 50)
    
    from generate_data import generate_dataset
    
    print("\ngenerating local data...")
    users, stations, trips, events = generate_dataset(num_users=100, num_stations=10, num_trips=500)
    
    print("starting spark session...")
    spark = SparkSession.builder \
        .appName("mobility_query2_fallback") \
        .getOrCreate()
    
    print("creating spark dataframes...")
    
    users_df = spark.createDataFrame(users)
    trips_df = spark.createDataFrame(trips)
    
    print(f"loaded {trips_df.count()} trips and {users_df.count()} users")
    
    print("\ncomputing trip stats per user...")
    trip_stats = trips_df.groupBy("user_id") \
        .agg(
            count("*").alias("trip_count"),
            avg("duration_minutes").alias("avg_duration")
        )
    
    print("joining with users...")
    result = users_df.join(
        trip_stats,
        "user_id",
        "left_outer"
    ).select(
        "user_id",
        "name",
        "surname",
        "country",
        coalesce(trip_stats["trip_count"], lit(0)).alias("trip_count"),
        coalesce(trip_stats["avg_duration"], lit(0)).alias("avg_duration")
    ).orderBy(col("trip_count").desc())
    
    print("\nresults:")
    result.show(15, truncate=False)
    
    spark.stop()
    print("\nspark session stopped.")


if __name__ == "__main__":
    spark_query2()