import subprocess
import time

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
    print("=== 1. Ingestion World Bank → BigQuery ===")
    avec_retry(ingest_data, essais=3, delai=5)

    print("\n=== 2. Transformation dbt ===")
    subprocess.run(
        ["uv", "run", "dbt", "run"],
        cwd="world_bank_group",  # Assure-toi que ce nom de dossier est exact
        check=True,
    )

    print("\n✅ Pipeline terminé : données ingérées et transformées.")