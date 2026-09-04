select distinct
    {{ dbt_utils.generate_surrogate_key(['indicator_id']) }} as indicator_key,
    indicator_id,
    indicator_name,
    unit
from {{ ref('stg_world_bank') }}
where indicator_id is not null