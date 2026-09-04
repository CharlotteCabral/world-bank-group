{{ config(
    materialized='table'
) }}

WITH staging AS (
    SELECT * 
    FROM {{ ref('stg_world_bank') }}
),

dim_country AS (
    SELECT country_code 
    FROM {{ ref('dim_country') }}
),

dim_year AS (
    SELECT year_key 
    FROM {{ ref('dim_year') }}
),

dim_indicator AS (
    SELECT indicator_code 
    FROM {{ ref('dim_indicator') }}
)

SELECT
    s.surrogate_key,
    s.country_code,
    s.annee,
    s.indicator_id AS indicator_code,
    s.valeur
FROM staging s
INNER JOIN dim_country c 
    ON s.country_code = c.country_code
INNER JOIN dim_year y 
    ON s.annee = y.year_key
INNER JOIN dim_indicator i 
    ON s.indicator_id = i.indicator_code
WHERE s.valeur IS NOT NULL
