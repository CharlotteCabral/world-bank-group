with source as (

    select *
    from {{ source('world_bank', 'raw_data') }}

),

renamed as (

    select
        country_name,
        countryiso3code,
        annee,

        PIB as pib,
        PIB_par_habitant as pib_par_habitant,
        Croissance_PIB as croissance_pib,
        Population as population,
        Esperance_vie as esperance_vie,
        Chomage as chomage,
        Inflation as inflation,
        Acces_electricite as acces_electricite,
        Taux_natalite as taux_natalite,
        Scolarisation_secondaire as scolarisation_secondaire,
        Scolarisation_superieur as scolarisation_superieur,
        Achevement_primaire as achevement_primaire,
        Depense_de_sante as depense_de_sante,
        Depense_publique_education as depense_publique_education,
        Alphabetisation_adultes as alphabetisation_adultes,

        row_hash,
        inserted_at

    from source

)

select *
from renamed