-- models/new_test_model.sql
SELECT customer_id, COUNT(*) AS order_count
FROM {{ ref('clean_orders') }}
GROUP BY customer_id
