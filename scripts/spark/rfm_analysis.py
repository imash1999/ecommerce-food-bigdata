import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType,
    DoubleType, ArrayType
)


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
        .appName("EcommerceRFMAnalysisFromS3") \
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
    print(f"Reade in SeaweedFS: {s3_path}")

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

    try:
        events_df = spark.read \
            .schema(order_schema) \
            .option("recursiveFileLookup", "true") \
            .json(s3_path)
    except Exception as e:
        print(f"Error reading SeaweedFS: {e}")
        spark.stop()
        return

    orders_df = events_df \
        .filter(F.col("event_type") == "order_created") \
        .withColumn("created_at", F.to_timestamp(F.col("timestamp"))) \
        .filter(F.col("created_at").isNotNull())

    count = orders_df.count()
    print(f"Найдено заказов: {count}")

    if count == 0:
        print("Have not orders")
        spark.stop()
        return

    max_timestamp = orders_df.select(F.max("created_at")).collect()[0][0]
    print(f"Max timestamp: {max_timestamp}")

    rfm_raw = orders_df.groupBy("user_id").agg(
        F.datediff(
            F.lit(max_timestamp),
            F.max("created_at")
        ).alias("recency_days"),
        F.count("event_id").alias("frequency"),
        F.sum("total_amount").alias("monetary")
    )

    r_window = Window.orderBy(F.col("recency_days").desc())
    f_window = Window.orderBy(F.col("frequency").asc())
    m_window = Window.orderBy(F.col("monetary").asc())

    rfm_scores = rfm_raw \
        .withColumn("r_score", F.ntile(5).over(r_window)) \
        .withColumn("f_score", F.ntile(5).over(f_window)) \
        .withColumn("m_score", F.ntile(5).over(m_window))

    rfm_segmented = rfm_scores.withColumn(
        "segment",
        F.when(
            (F.col("r_score") >= 4) & (F.col("f_score") >= 4),
            "Champions"
        )
        .when(
            (F.col("r_score") >= 3) & (F.col("f_score") >= 3),
            "Loyal Customers"
        )
        .when(
            (F.col("r_score") >= 3) & (F.col("f_score") < 3),
            "Promising / Recent"
        )
        .when(
            (F.col("r_score") < 3) & (F.col("f_score") >= 3),
            "At Risk"
        )
        .otherwise("Lost / Hibernating")
    ).withColumn("calculated_at", F.current_timestamp())

    print("Write result to PostgreSQL table: user_rfm_segments")

    rfm_segmented.write \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "user_rfm_segments") \
        .option("user", postgres_user) \
        .option("password", postgres_password) \
        .option("driver", "org.postgresql.Driver") \
        .option("truncate", "true") \
        .mode("overwrite") \
        .save()

    print("RFM finished!")
    spark.stop()


if __name__ == "__main__":
    main()