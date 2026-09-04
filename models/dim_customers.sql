SELECT
  customer_id,
  customer_unique_id,
  customer_city,
  customer_state
FROM {{ source('olist', 'olist_customers') }}
