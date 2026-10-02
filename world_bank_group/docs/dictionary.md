## Dictionnaire de données (`predictions`)

| Colonne | Type | Description | Exemple |
| :--- | :--- | :--- | :--- |
| `country_name` | Chaîne (STRING) | Nom officiel du pays | `France` |
| `pib` | Décimal (FLOAT) | Produit Intérieur Brut (en USD) | `30054188271.34` |
| `chomage` | Décimal (FLOAT) | Taux de chômage total (% de la population active) | `7.8` |
| `inflation` | Décimal (FLOAT) | Taux d'inflation annuel (prix à la consommation) | `2.1` |
| `esperance_vie` | Décimal (FLOAT) | Espérance de vie à la naissance (en années) | `82.5` |
| `scolarisation_secondaire` | Décimal (FLOAT) | Taux de scolarisation dans le secondaire (%) | `98.2` |
| `co2_par_habitant` | Décimal (FLOAT) | Émissions de CO2 par habitant (en tonnes) | `4.5` |
| `cluster_id` | Entier (INTEGER) | Numéro du cluster attribué par le modèle K-Means | `1` |
| `silhouette_score_global` | Décimal (FLOAT) | Score global de qualité du clustering | `0.4521` |
| `date_prediction` | Horodatage (TIMESTAMP) | Date et heure de l'exécution du pipeline de prédiction | `2026-09-29 12:00:00` |