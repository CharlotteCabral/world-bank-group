# Schéma de la base de données (BigQuery)

Ce schéma présente l'architecture complète des tables d'ingestion, des transformations dbt (`world_bank_marts`) et de la table finale de prédictions du modèle de Machine Learning (`ml_world_bank`)

## Diagramme des relations (Modèle Logique)

```mermaid
erDiagram
    dim_country ||--o{ fact_country_indicators : "1,N"
    dim_indicator ||--o{ fact_country_indicators : "1,N"
    dim_year ||--o{ fact_country_indicators : "1,N"
    dim_country ||--o| pays_features : "1,1"
    pays_features ||--o| predictions : "1,1"

    dim_country {
        string country_code PK "Code ISO à 3 lettres du pays"
        string country_name "Nom officiel du pays"
        string region "Région du monde"
    }

    dim_indicator {
        string indicator_code PK "Code de l'indicateur (ex: NY.GDP.PCAP.CD)"
        string indicator_name "Libellé de l'indicateur"
    }

    dim_year {
        int year PK "Année de la mesure"
    }

    fact_country_indicators {
        string surrogate_key PK "Clé unique de la ligne"
        string country_code FK "Référence vers dim_country"
        string indicator_code FK "Référence vers dim_indicator"
        int year FK "Référence vers dim_year"
        float value "Valeur numérique brute de l'indicateur"
    }

    pays_features {
        string country_name PK "Nom du pays"
        float pib "PIB en USD (pivoté)"
        float chomage "Taux de chômage (pivoté)"
        float inflation "Taux d'inflation (pivoté)"
        float esperance_vie "Espérance de vie (pivoté)"
        float scolarisation_secondaire "Taux de scolarisation (pivoté)"
        float co2_par_habitant "Émissions CO2 par habitant (pivoté)"
    }

    predictions {
        string country_name PK "Nom du pays"
        float pib "PIB en USD"
        float chomage "Taux de chômage"
        float inflation "Taux d'inflation"
        float esperance_vie "Espérance de vie"
        float scolarisation_secondaire "Taux de scolarisation"
        float co2_par_habitant "Émissions CO2"
        int cluster_id "Numéro du cluster K-Means attribué"
        float silhouette_score_global "Score global de qualité du clustering"
        timestamp date_prediction "Horodatage de l'exécution du run"
    }