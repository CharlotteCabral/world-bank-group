import joblib
from datetime import datetime, timezone
from google.cloud import bigquery
from sklearn.metrics import silhouette_score
import os
if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ and os.path.exists("C:\\dev\\cle_bigquery.json"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\dev\\cle_bigquery.json"

PROJECT = "data-quest-charlotte-504508"  
MARTS = "world_bank_marts"
FEATURES = "pays_features"  
ML = "ml_world_bank"

def predire():
    client = bigquery.Client(project=PROJECT)
    
    print("1. Lecture des données propres depuis BigQuery...")
    query = f"""
        SELECT country_name, pib, chomage, inflation, esperance_vie, scolarisation_secondaire, co2_par_habitant
        FROM `{PROJECT}.{MARTS}.{FEATURES}`
    """
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    
    print("2. Application du modèle de clustering (pipeline.pkl)...")
    pipeline = joblib.load("pipeline.pkl")
    
    features_cols = ["pib", "chomage", "inflation", "esperance_vie", "scolarisation_secondaire", "co2_par_habitant"]
    
    # Application des prédictions sur tout le df
    df["cluster_id"] = pipeline.predict(df[features_cols])
    print(df["cluster_id"].value_counts())
    
    # On isole un sous-ensemble sans NaN uniquement pour calculer le score de silhouette
    df_eval = df.dropna(subset=features_cols)
    
    # Sécurité : la silhouette nécessite au moins 2 clusters différents pour être calculée
    if len(df_eval["cluster_id"].unique()) > 1:
        score = silhouette_score(df_eval[features_cols], df_eval["cluster_id"])
        print(f"-> Score de silhouette du clustering : {score:.4f}")
    else:
        score = 0.0
        print("-> Avertissement : Un seul cluster détecté, score de silhouette non calculable.")
    
    # Ajout du score global dans ton df principal
    df["silhouette_score_global"] = score
    
    df["date_prediction"] = datetime.now(timezone.utc)
    
    print(f"3. Écriture de {len(df)} lignes dans `{PROJECT}.{ML}.predictions`...")
    
    # WRITE_TRUNCATE écrase la table à chaque run pour éviter les doublons dans Power BI
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE"
      )

    client.load_table_from_dataframe(
        df,
        f"{PROJECT}.{ML}.predictions",
        job_config=job_config,
    ).result()
    
    print("Clustering terminé et sauvegardé avec succès dans BigQuery !")

if __name__ == "__main__":
    predire()