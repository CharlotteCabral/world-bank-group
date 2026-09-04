import datetime
import hashlib
import json
import time
from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
from google.cloud import bigquery
import requests

# 1. Chargement des variables d'environnement (.env)
load_dotenv()

# Instanciation automatique du client BigQuery
client = bigquery.Client()

DATASET_ID = "world_bank_raw"
TABLE_ID = f"{client.project}.{DATASET_ID}.raw_data"

INDICATORS = [
    "NY.GDP.MKTP.CD",
    "NY.GDP.PCAP.CD",
    "NY.GDP.MKTP.KD.ZG",
    "SP.POP.TOTL",
    "SP.DYN.LE00.IN",
    "SL.UEM.TOTL.ZS",
    "FP.CPI.TOTL.ZG",
    "EG.ELC.ACCS.ZS",
    "EN.ATM.CO2E.PC",
    "SP.DYN.CBRT.IN",
    "SE.SEC.ENRR",
    "SE.TER.ENRR",
    "SE.PRM.CMPT.ZS",
    "SH.XPD.CHEX.GD.ZS",
    "SE.XPD.TOTL.GD.ZS",
    "SE.ADT.LITR.ZS",
]


def generate_surrogate_key(record: dict) -> str:
    """Génère une surrogate key basée sur Pays + Année + Indicateur."""
    country = record.get("countryiso3code") or ""
    date = record.get("date") or ""
    indicator_obj = record.get("indicator") or {}
    indicator_id = indicator_obj.get("id") or ""

    raw_key = f"{country}_{date}_{indicator_id}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def get_existing_hashes() -> set:
    """Récupère les hashs existants dans BigQuery pour éviter les doublons."""
    query = f"""
        SELECT `hash`
        FROM `{TABLE_ID}` 
        ORDER BY inserted_at DESC 
        LIMIT 100000
    """
    try:
        query_job = client.query(query)
        return {row["hash"] for row in query_job}
    except NotFound:
        print("ℹ️ La table n'existe pas encore. Elle sera créée à la première insertion.")
        return set()


def fetch_indicator_data(code: str) -> list[dict]:
    """Récupère tous les enregistrements bruts avec gestion de la pagination."""
    records = []
    page = 1
    pages_total = 1

    while page <= pages_total:
        url = f"https://api.worldbank.org/v2/country/all/indicator/{code}"
        params = {"format": "json", "per_page": 2000, "page": page}

        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code != 200:
                print(f"❌ {code} (Page {page}) : HTTP {response.status_code}")
                break

            data = response.json()
            if not isinstance(data, list) or len(data) < 2 or not isinstance(data[0], dict):
                print(f"❌ {code} (Page {page}) : Structure JSON invalide")
                break

            pages_total = data[0].get("pages", 1)
            raw_records = data[1]

            if raw_records:
                records.extend(raw_records)

            page += 1
            time.sleep(0.2)

        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"❌ {code} (Page {page}) : Erreur -> {e}")
            break

    return records


def ingest_data():
    existing_hashes = get_existing_hashes()
    records_to_insert = []
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for code in INDICATORS:
        print(f"🔄 Récupération de l'indicateur : {code}...")
        raw_records = fetch_indicator_data(code)

        for record in raw_records:
            # Hash global du payload (pour détecter un changement de valeur)
            serialized = json.dumps(record, sort_keys=True)
            record_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

            # Clé surrogate métier (Pays + Année + Indicateur)
            surrogate_key = generate_surrogate_key(record)

            if record_hash not in existing_hashes:
                existing_hashes.add(record_hash)

                records_to_insert.append(
                    {
                        "surrogate_key": surrogate_key,
                        "hash": record_hash,
                        "inserted_at": now_iso,
                        "payload": json.dumps(record),
                    }
                )

    print(f"📦 Nouveaux enregistrements à insérer : {len(records_to_insert)}")

    if records_to_insert:
        # 1. Définition explicite du schéma de la table brute
        schema = [
            bigquery.SchemaField("surrogate_key", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("hash", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("inserted_at", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("payload", "STRING", mode="NULLABLE"),
        ]

        # 2. Création de la table si elle n'existe pas encore
        table = bigquery.Table(TABLE_ID, schema=schema)
        client.create_table(table, exists_ok=True)

        # 3. Chargement des données
        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        )

        job = client.load_table_from_json(
            records_to_insert, TABLE_ID, job_config=job_config
        )
        job.result()
        print("✅ Ingestion réussie dans BigQuery !")


if __name__ == "__main__":
    ingest_data()