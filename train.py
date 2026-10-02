import joblib
from google.cloud import bigquery
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\dev\\cle_bigquery.json"
# Configuration
PROJECT = "data-quest-charlotte-504508"
MARTS = "world_bank_marts"
FEATURES = "pays_features"

def entrainer_modele():
    print("1. Connexion à BigQuery et récupération des features...")
    client = bigquery.Client(project=PROJECT)
    
    query = f"""
        SELECT country_name, pib, chomage, inflation, esperance_vie, scolarisation_secondaire, co2_par_habitant
        FROM `{PROJECT}.{MARTS}.{FEATURES}`
    """
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    
    # Nettoyage rapide si des valeurs manquantes existent
    df = df.fillna(0)
    
    # Définition des colonnes numériques utilisées pour le clustering
    features_cols = ["pib", "chomage", "inflation", "esperance_vie", "scolarisation_secondaire", "co2_par_habitant"]
    X = df[features_cols]
    
    print("2. Création du pipeline (SimpleImputer + StandardScaler + KMeans)...")
    pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='mean')),
    ('scaler', StandardScaler()),
    ('kmeans', KMeans(n_clusters=3, random_state=42))
])
    
    print("3. Entraînement du modèle...")
    pipeline.fit(X)
    
    print("4. Sauvegarde du modèle dans pipeline.pkl...")
    joblib.dump(pipeline, "pipeline.pkl")
    
    print("Modèle entraîné et fichier 'pipeline.pkl' généré avec succès !")

if __name__ == "__main__":
    entrainer_modele()