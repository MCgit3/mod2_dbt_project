-- Fact table: one row per order
WITH order_items AS (

    SELECT
        order_id,
        COUNT(*) AS item_count,
        SUM(price) AS total_item_value,
        SUM(freight_value) AS total_freight_value
    FROM {{ source('olist', 'olist_order_items') }}
    GROUP BY order_id

),

payments AS (

    SELECT
        order_id,
        SUM(payment_value) AS total_payment_value
    FROM {{ source('olist', 'olist_order_payments') }}
    GROUP BY order_id

)

SELECT
    o.order_id,
    o.customer_id,
    o.order_purchase_timestamp AS order_date,
    COALESCE(oi.item_count, 0) AS item_count,
    COALESCE(oi.total_item_value, 0) AS total_item_value,
    COALESCE(oi.total_freight_value, 0) AS total_freight_value,
    COALESCE(p.total_payment_value, 0) AS total_payment_value

FROM {{ ref('clean_orders') }} o

LEFT JOIN order_items oi
    ON o.order_id = oi.order_id

LEFT JOIN payments p
    ON o.order_id = p.order_id

