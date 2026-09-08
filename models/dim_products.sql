-- Dimension table: products
SELECT DISTINCT
    product_id,
    product_category_name
FROM {{ source('olist', 'olist_products') }}
