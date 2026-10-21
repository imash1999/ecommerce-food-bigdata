SET 'execution.runtime-mode' = 'streaming';
SET 'execution.target' = 'remote';
SET 'jobmanager.rpc.address' = 'flink-jobmanager';

CREATE TABLE order_events (
    event_id STRING,
    event_type STRING,
    user_id INT,
    restaurant_id INT,
    total_amount DECIMAL(10,2),
    status STRING,
    `timestamp` TIMESTAMP(3),
    WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'order-events',
    'properties.bootstrap.servers' = 'kafka:29092',
    'properties.group.id' = 'order-metrics-group',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json'
);


CREATE TABLE postgres_sink (
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    total_orders BIGINT,
    total_revenue DECIMAL(12,2),
    avg_order_amount DECIMAL(12,2)
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:postgresql://postgres:5432/postgres',
    'table-name' = 'realtime_order_metrics',
    'username' = 'postgres',
    'password' = 'root'
);


INSERT INTO postgres_sink
SELECT
    TUMBLE_START(`timestamp`, INTERVAL '1' MINUTE),
    TUMBLE_END(`timestamp`, INTERVAL '1' MINUTE),
    COUNT(*),
    SUM(total_amount),
    AVG(total_amount)
FROM order_events
GROUP BY TUMBLE(`timestamp`, INTERVAL '1' MINUTE);
