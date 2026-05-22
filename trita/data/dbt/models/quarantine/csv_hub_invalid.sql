select
    tenant_id,
    upload_id,
    source,
    entity_type,
    row_number,
    error_code,
    raw_snippet,
    created_at
from quarantine.csv_hub
