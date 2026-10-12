import os
import json
from datetime import datetime
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings

def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    
    KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "root")

    
    t_env.execute_sql(f"""
        CREATE TABLE kafka_events (
            event_id STRING,
            user_id STRING,
            item_id STRING,
            category STRING,
            action STRING,
            price DECIMAL(10, 2),
            `timestamp` TIMESTAMP(3),
            WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'ecommerce-events',
            'properties.bootstrap.servers' = '{KAFKA_SERVERS}',
            'properties.group.id' = 'flink-metrics-group',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json'
        )
    """)

    
    t_env.execute_sql(f"""
        CREATE TABLE postgres_sink (
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            total_views BIGINT,
            total_cart_adds BIGINT,
            total_buys BIGINT,
            total_revenue DECIMAL(10, 2)
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://{POSTGRES_HOST}:5432/{POSTGRES_DB}',
            'table-name' = 'realtime_metrics',
            'username' = '{POSTGRES_USER}',
            'password' = '{POSTGRES_PASSWORD}'
        )
    """)

    
    t_env.execute_sql("""
        INSERT INTO postgres_sink
        SELECT
            TUMBLE_START(`timestamp`, INTERVAL '1' MINUTE) AS window_start,
            TUMBLE_END(`timestamp`, INTERVAL '1' MINUTE) AS window_end,
            COUNT(CASE WHEN action = 'view' THEN 1 END) AS total_views,
            COUNT(CASE WHEN action = 'add_to_cart' THEN 1 END) AS total_cart_adds,
            COUNT(CASE WHEN action = 'buy' THEN 1 END) AS total_buys,
            COALESCE(SUM(CASE WHEN action = 'buy' THEN price ELSE 0 END), 0.00) AS total_revenue
        FROM kafka_events
        GROUP BY TUMBLE(`timestamp`, INTERVAL '1' MINUTE)
    """)

iif __name__ == "__main__":
    main()