select
    tenant_id,
    channel_order_key,
    shopify_order_id,
    shopify_order_name,
    shipment_id,
    payment_id,
    settlement_id,
    has_shipment,
    has_payment,
    (has_shipment and has_payment) as has_full_bridge,
    updated_at
from public.order_bridge
