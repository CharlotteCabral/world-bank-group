# Guide d'utilisation du Tableau de Bord Power BI - World Bank Clustering

Ce document présente le guide d'utilisation du tableau de bord Power BI connecté à BigQuery, destiné à restituer les analyses socio-économiques et les clusters de pays issus du modèle K-Means.

## 1. Connexion aux données
Le tableau de bord se connecte directement à la table finale de prédictions stockée dans BigQuery :
- **Projet GCP / Dataset** : `ml_world_bank`
- **Table source** : `predictions`
- **Mode de connexion** : DirectQuery 

## 2. Structure et Pages du Tableau de Bord
Le rapport est divisé en plusieurs sections clés pour faciliter la lecture par les parties prenantes :
- **Vue d'ensemble mondiale** : 
  - Cartes interactives des pays colorées selon leur `cluster_id`.
  - Indicateurs clés (KPI) globaux : nombre de pays analysés, PIB moyen mondial, score de silhouette global du modèle.
- **Analyse détaillée par Cluster** :
  - Profils socio-économiques moyens de chaque cluster (PIB, chômage, inflation, espérance de vie,education, CO2).
  - Graphiques de dispersion pour comparer les corrélations entre les indicateurs.
- **Filtres croisés disponibles** :
  - Filtre dynamique par numéro de cluster.

## 3. Actualisation des données
Puisque le script `predict.py` intègre un mécanisme d'écriture propre (`WRITE_TRUNCATE`) pour éviter toute duplication de données dans BigQuery :
1. Exécuter le pipeline complet dans le terminal : `python run_pipeline.py`
2. Une fois les données rafraîchies dans BigQuery, ouvrir Power BI Desktop et cliquer sur le bouton **Actualiser** pour propager les dernières prédictions de clustering dans les visuels.