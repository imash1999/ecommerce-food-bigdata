CREATE TABLE IF NOT EXISTS realtime_metrics (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMP WITHOUT TIME ZONE,
    window_end TIMESTAMP WITHOUT TIME ZONE,
    total_views INT DEFAULT 0,
    total_cart_adds INT DEFAULT 0,
    total_buys INT DEFAULT 0,
    total_revenue NUMERIC(10, 2) DEFAULT 0.00,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS realtime_order_metrics (
    window_start TIMESTAMP WITHOUT TIME ZONE,
    window_end TIMESTAMP WITHOUT TIME ZONE,
    total_orders BIGINT,
    total_revenue NUMERIC(12, 2),
    avg_order_amount NUMERIC(12, 2)
);

CREATE TABLE IF NOT EXISTS rfm_analysis (
    user_id VARCHAR(64) PRIMARY KEY,
    recency INT,
    frequency INT,
    monetary NUMERIC(10, 2),
    rfm_score VARCHAR(10),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
