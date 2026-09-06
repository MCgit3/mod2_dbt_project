-- models/new_test_model.sql
SELECT order_id, COUNT(*) AS order_count
FROM {{ ref('clean_orders') }}
GROUP BY order_id