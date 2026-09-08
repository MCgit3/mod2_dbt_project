-- Dimension table: sellers
SELECT DISTINCT
    seller_id,
    seller_city,
    seller_state
FROM {{ source('olist', 'olist_sellers') }}
