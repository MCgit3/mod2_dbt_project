SELECT
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp
FROM {{ source('olist', 'olist_orders') }}
WHERE order_status IN (
    'delivered',
    'shipped',
    'processing',
    'invoiced'
)

