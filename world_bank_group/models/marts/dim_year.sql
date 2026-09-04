select distinct
    annee as year_key,
    annee as year_number
from {{ ref('stg_world_bank') }}
where annee is not null