select

    -- Surrogate key : identifiant unique pour chaque pays + année
    TO_HEX(
        MD5(
            CONCAT(
                CAST(countryiso3code AS STRING),
                '_',
                CAST(annee AS STRING)
            )
        )
    ) as country_year_key,
    
    country_name,
    countryiso3code,
    annee,

    pib,
    pib_par_habitant,
    croissance_pib,
    population,
    esperance_vie,
    chomage,
    inflation,
    acces_electricite,
    taux_natalite,
    scolarisation_secondaire,
    scolarisation_superieur,
    achevement_primaire,
    depense_de_sante,
    depense_publique_education,
    alphabetisation_adultes

from {{ ref('stg_world_bank') }}