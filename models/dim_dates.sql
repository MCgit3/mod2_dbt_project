-- Dimension table: dates
SELECT DISTINCT
    DATE(order_purchase_timestamp) AS order_date,
    EXTRACT(YEAR FROM order_purchase_timestamp) AS year,
    EXTRACT(MONTH FROM order_purchase_timestamp) AS month,
    EXTRACT(DAY FROM order_purchase_timestamp) AS day,
    EXTRACT(DAYOFWEEK FROM order_purchase_timestamp) AS weekday
FROM {{ ref('clean_orders') }}

