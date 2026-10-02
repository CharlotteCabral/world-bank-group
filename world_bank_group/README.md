# World Bank Socio-Economic Clustering

Pipeline ELT, transformation dbt et Machine Learning pour analyser et cartographier les profils socio-économiques mondiaux.

## Prérequis
- Python 3.11[cite: 7]
- Une clé de service pour accéder à BigQuery
- Power BI Desktop

## Installation
pip install -r requirements.txt  

## Utilisation
python run_pipeline.py  # lance l'ingestion, dbt, le ML et les prédictions

## Structure du projet
- load_data.py : ingestion incrémentale des données depuis l'API de la Banque Mondiale
- models/ : transformations et modélisation des données avec dbt (staging et marts)
- predict.py : application du modèle de clustering K-Means et écriture dans BigQuery
- dashboard/ : le tableau de bord Power BI

## Sources de données
API publique de la Banque Mondiale (indicateurs macro-économiques, démographiques et environnementaux).

## Contact
charlottecabral@yahoo.fr

