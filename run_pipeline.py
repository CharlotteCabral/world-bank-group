import subprocess
import time
from train import entrainer_modele  # 👈 Importe la fonction d'entraînement
from predict import predire
from load_data import ingest_data


def avec_retry(action, essais=3, delai=5):
    """Lance une action et réessaie en cas d'erreur."""
    for tentative in range(1, essais + 1):
        try:
            return action()
        except Exception as e:
            print(f"⚠️ Échec (tentative {tentative}/{essais}) : {e}")
            if tentative < essais:
                print(f"↻ Nouvel essai dans {delai} secondes...")
                time.sleep(delai)

    raise RuntimeError(f"Abandon après {essais} tentatives.")

if __name__ == "__main__":
    print("=== 1. Ingestion World Bank -> BigQuery ===")
    avec_retry(ingest_data, essais=3, delai=5)
    
    print("\n=== 2. Transformation dbt ===")
    subprocess.run(["dbt", "run"], cwd="world_bank_group", check=True)
    
    print("\n=== 3. Entraînement du modèle ML ===")
    entrainer_modele() 
    
    print("\n=== 4. Prédiction ML ===")
    predire()
    
    print("\n✅ Pipeline terminé : données ingérées, transformées, modélisées et prédites.")