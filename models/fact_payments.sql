SELECT
  o.order_id,
  o.customer_id,
  p.payment_type,
  p.payment_value,
  p.payment_installments
FROM {{ ref('clean_orders') }} o
JOIN {{ source('olist', 'olist_order_payments') }} p
  ON o.order_id = p.order_id
