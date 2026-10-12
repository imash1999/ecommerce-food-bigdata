import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType,
    DoubleType, ArrayType
)
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator


def main():
    postgres_host = os.getenv("POSTGRES_HOST", "postgres")
    postgres_db = os.getenv("POSTGRES_DB", "postgres")
    postgres_user = os.getenv("POSTGRES_USER", "postgres")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "root")
    jdbc_url = f"jdbc:postgresql://{postgres_host}:5432/{postgres_db}"

    s3_endpoint = os.getenv("S3_ENDPOINT", "http://seaweedfs:9000")
    s3_access_key = os.getenv("S3_ACCESS_KEY", "seaweedfs")
    s3_secret_key = os.getenv("S3_SECRET_KEY", "seaweedfs")
    s3_bucket = os.getenv("S3_BUCKET", "raw-events")
    s3_prefix = os.getenv("S3_PREFIX", "orders/")

    spark = SparkSession.builder \
        .appName("EcommerceRecommendations") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    hadoop_conf = spark._jsc.hadoopConfiguration()
    hadoop_conf.set("fs.s3a.endpoint", s3_endpoint)
    hadoop_conf.set("fs.s3a.access.key", s3_access_key)
    hadoop_conf.set("fs.s3a.secret.key", s3_secret_key)
    hadoop_conf.set("fs.s3a.path.style.access", "true")
    hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    hadoop_conf.set(
        "fs.s3a.aws.credentials.provider",
        "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider"
    )

    s3_path = f"s3a://{s3_bucket}/{s3_prefix}*"
    print(f"Read orders SeaweedFS: {s3_path}")

    order_schema = StructType([
        StructField("event_id", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("user_id", LongType(), True),
        StructField("restaurant_id", LongType(), True),
        StructField("items", ArrayType(
            StructType([
                StructField("dish_id", LongType(), True),
                StructField("name", StringType(), True),
                StructField("quantity", LongType(), True),
                StructField("unit_price", DoubleType(), True),
            ])
        ), True),
        StructField("total_amount", DoubleType(), True),
        StructField("status", StringType(), True),
        StructField("timestamp", StringType(), True),
    ])

    events_df = spark.read \
        .schema(order_schema) \
        .option("recursiveFileLookup", "true") \
        .json(s3_path)

    orders_df = events_df.filter(F.col("event_type") == "order_created")

    total_orders = orders_df.count()
    print(f"Total orders: {total_orders}")

    interactions_df = orders_df \
        .select(
            F.col("user_id"),
            F.explode("items").alias("item")
        ) \
        .select(
            F.col("user_id"),
            F.col("item.dish_id").alias("dish_id"),
            F.col("item.quantity").alias("quantity")
        ) \
        .filter(F.col("dish_id").isNotNull()) \
        .groupBy("user_id", "dish_id") \
        .agg(F.sum("quantity").cast("float").alias("rating"))

    count = interactions_df.count()

    if count < 50:
        print("Insufficient data for ALS. Exit.")
        spark.stop()
        return

    (training, test) = interactions_df.randomSplit([0.8, 0.2], seed=42)

    print("ALS training")

    als = ALS(
        userCol="user_id",
        itemCol="dish_id",
        ratingCol="rating",
        rank=10,
        maxIter=10,
        regParam=0.01,
        coldStartStrategy="drop",
        nonnegative=True
    )

    model = als.fit(training)

    predictions = model.transform(test)
    evaluator = RegressionEvaluator(
        metricName="rmse",
        labelCol="rating",
        predictionCol="prediction"
    )
    rmse = evaluator.evaluate(predictions)
    print(f"RMSE: {rmse:.4f}")

    print("Generating recommendations")

    user_recs = model.recommendForAllUsers(5)

    recs_df = user_recs \
        .select(
            F.col("user_id"),
            F.explode("recommendations").alias("rec")
        ) \
        .select(
            F.col("user_id"),
            F.col("rec.dish_id").alias("dish_id"),
            F.col("rec.rating").alias("score")
        ) \
        .withColumn(
            "rank",
            F.row_number().over(
                Window.partitionBy("user_id").orderBy(F.col("score").desc())
            )
        ) \
        .withColumn("calculated_at", F.current_timestamp())

    dishes_df = spark.read \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "dishes") \
        .option("user", postgres_user) \
        .option("password", postgres_password) \
        .option("driver", "org.postgresql.Driver") \
        .load() \
        .select(
            F.col("id").alias("dish_id"),
            F.col("name").alias("dish_name"),
            F.col("image_url")
        )
    recs_with_names = recs_df.join(
        dishes_df, on="dish_id", how="left"
    ).select(
        "user_id", "dish_id", "dish_name", "image_url",
        "score", "rank", "calculated_at"
    )

    print("Запись в PostgreSQL (таблица user_recommendations)...")

    recs_with_names.write \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "user_recommendations") \
        .option("user", postgres_user) \
        .option("password", postgres_password) \
        .option("driver", "org.postgresql.Driver") \
        .option("truncate", "true") \
        .mode("overwrite") \
        .save()

    print("Recommendations successfully generated!")
    spark.stop()


if __name__ == "__main__":
    main()