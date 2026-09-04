with source as (
    select distinct
        indicator_id as indicator_code,
        indicator_name
    from {{ ref('stg_world_bank') }}
    where indicator_id is not null
)

select
    indicator_code,
    indicator_name,
    case indicator_code
        when 'SE.SEC.ENRR' then 'Scolarisation_secondaire'
        when 'SE.TER.ENRR' then 'Scolarisation_superieur'
        when 'SP.DYN.CBRT.IN' then 'Taux_natalite'
        when 'SP.DYN.LE00.IN' then 'Esperance_vie'
        when 'EN.GHG.CO2.PC.CE.AR5' then 'CO2_par_habitant'
        when 'FP.CPI.TOTL.ZG' then 'Inflation'
        when 'SE.XPD.TOTL.GD.ZS' then 'Depense_publique_education'
        when 'SE.ADT.LITR.ZS' then 'Alphabetisation_adultes'
        when 'SL.UEM.TOTL.ZS' then 'Chomage'
        when 'SH.XPD.CHEX.GD.ZS' then 'Depense_de_sante'
        when 'NY.GDP.MKTP.KD.ZG' then 'Croissance_PIB'
        when 'NY.GDP.PCAP.CD' then 'PIB_par_habitant'
        when 'SP.POP.TOTL' then 'Population'
        when 'SE.PRM.CMPT.ZS' then 'Achevement_primaire'
        when 'NY.GDP.MKTP.CD' then 'PIB'
        when 'EG.ELC.ACCS.ZS' then 'Acces_electricite'
        else indicator_name
    end as indicator_label_fr,
    cast(null as string) as unit
from source
