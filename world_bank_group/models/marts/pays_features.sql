{{ config(
    materialized='table'
) }}

WITH base_indicators AS (
    SELECT
        s.country_code,
        c.country_name,
        s.annee,
        s.indicator_code,
        s.valeur
    FROM {{ ref('fact_country_indicators') }} s
    -- On joint avec dim_country pour récupérer le nom propre du pays si besoin
    LEFT JOIN {{ ref('dim_country') }} c 
        ON s.country_code = c.country_code
)

-- On pivote les lignes en colonnes pour avoir une seule ligne par pays
SELECT
    country_code,
    MAX(country_name) AS country_name,
    MAX(CASE WHEN indicator_code = 'NY.GDP.MKTP.CD' THEN valeur END) AS pib,
    MAX(CASE WHEN indicator_code = 'NY.GDP.PCAP.CD' THEN valeur END) AS pib_par_habitant,
    MAX(CASE WHEN indicator_code = 'NY.GDP.MKTP.KD.ZG' THEN valeur END) AS croissance_pib,
    MAX(CASE WHEN indicator_code = 'SP.POP.TOTL' THEN valeur END) AS population,
    MAX(CASE WHEN indicator_code = 'SP.DYN.LE00.IN' THEN valeur END) AS esperance_vie,
    MAX(CASE WHEN indicator_code = 'SL.UEM.TOTL.ZS' THEN valeur END) AS chomage,
    MAX(CASE WHEN indicator_code = 'FP.CPI.TOTL.ZG' THEN valeur END) AS inflation,
    MAX(CASE WHEN indicator_code = 'EG.ELC.ACCS.ZS' THEN valeur END) AS acces_electricite,
    MAX(CASE WHEN indicator_code = 'EN.GHG.CO2.PC.CE.AR5' THEN valeur END) AS co2_par_habitant,
    MAX(CASE WHEN indicator_code = 'SP.DYN.CBRT.IN' THEN valeur END) AS taux_natalite,
    MAX(CASE WHEN indicator_code = 'SE.SEC.ENRR' THEN valeur END) AS scolarisation_secondaire,
    MAX(CASE WHEN indicator_code = 'SE.TER.ENRR' THEN valeur END) AS scolarisation_superieure,
    MAX(CASE WHEN indicator_code = 'SE.PRM.CMPT.ZS' THEN valeur END) AS achevement_primaire,
    MAX(CASE WHEN indicator_code = 'SH.XPD.CHEX.GD.ZS' THEN valeur END) AS depense_de_sante,
    MAX(CASE WHEN indicator_code = 'SE.XPD.TOTL.GD.ZS' THEN valeur END) AS depense_publique_education,
    MAX(CASE WHEN indicator_code = 'SE.ADT.LITR.ZS' THEN valeur END) AS alphabetisation_adultes
FROM base_indicators

GROUP BY country_code