with source as (
    select * from {{ ref('stg_world_bank') }}
)

select
    -- Clés étrangères (Foreign Keys) vers les dimensions
    {{ dbt_utils.generate_surrogate_key(['country_iso3']) }} as country_key,
    annee as year_key,
    
    -- Métriques (16 indicateurs pivoités)
    max(case when indicator_id = 'NY.GDP.MKTP.CD' then valeur end) as pib,
    max(case when indicator_id = 'NY.GDP.PCAP.CD' then valeur end) as pib_par_habitant,
    max(case when indicator_id = 'NY.GDP.MKTP.KD.ZG' then valeur end) as croissance_pib,
    max(case when indicator_id = 'SP.POP.TOTL' then valeur end) as population,
    max(case when indicator_id = 'SP.DYN.LE00.IN' then valeur end) as esperance_vie,
    max(case when indicator_id = 'SL.UEM.TOTL.ZS' then valeur end) as chomage,
    max(case when indicator_id = 'FP.CPI.TOTL.ZG' then valeur end) as inflation,
    max(case when indicator_id = 'EG.ELC.ACCS.ZS' then valeur end) as acces_electricite,
    max(case when indicator_id = 'EN.ATM.CO2E.PC' then valeur end) as co2_par_habitant,
    max(case when indicator_id = 'SP.DYN.CBRT.IN' then valeur end) as taux_natalite,
    max(case when indicator_id = 'SE.SEC.ENRR' then valeur end) as scolarisation_secondaire,
    max(case when indicator_id = 'SE.TER.ENRR' then valeur end) as scolarisation_superieur,
    max(case when indicator_id = 'SE.PRM.CMPT.ZS' then valeur end) as achevement_primaire,
    max(case when indicator_id = 'SH.XPD.CHEX.GD.ZS' then valeur end) as depense_de_sante,
    max(case when indicator_id = 'SE.XPD.TOTL.GD.ZS' then valeur end) as depense_publique_education,
    max(case when indicator_id = 'SE.ADT.LITR.ZS' then valeur end) as alphabetisation_adultes

from source
group by 
    country_iso3,
    annee
