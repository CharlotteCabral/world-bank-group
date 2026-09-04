import datetime
import hashlib
import json
import time
from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
from google.cloud import bigquery
import requests

load_dotenv()

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
    "EN.GHG.CO2.PC.CE.AR5", 
    "SP.DYN.CBRT.IN",
    "SE.SEC.ENRR",
    "SE.TER.ENRR",
    "SE.PRM.CMPT.ZS",
    "SH.XPD.CHEX.GD.ZS",
    "SE.XPD.TOTL.GD.ZS",
    "SE.ADT.LITR.ZS",
]


def generate_surrogate_key(record: dict) -> str:
    country = record.get("countryiso3code") or ""
    date = record.get("date") or ""
    indicator_obj = record.get("indicator") or {}
    indicator_id = indicator_obj.get("id") or ""

    raw_key = f"{country}_{date}_{indicator_id}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def fetch_indicator_data(code: str) -> list[dict]:
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
                print(f"⚠️ {code} (Page {page}) : Pas de données renvoyées par l'API")
                break

            pages_total = data[0].get("pages", 1)
            raw_records = data[1]

            if raw_records:
                records.extend(raw_records)

            page += 1
            time.sleep(0.1)

        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"❌ {code} (Page {page}) : Erreur -> {e}")
            break

    return records


def ingest_data():
    records_to_insert = []
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for code in INDICATORS:
        print(f"🔄 Récupération : {code}...")
        raw_records = fetch_indicator_data(code)
        print(f"   ↳ {len(raw_records)} lignes récupérées.")

        for record in raw_records:
            serialized = json.dumps(record, sort_keys=True)
            record_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
            surrogate_key = generate_surrogate_key(record)

            records_to_insert.append(
                {
                    "surrogate_key": surrogate_key,
                    "hash": record_hash,
                    "inserted_at": now_iso,
                    "payload": json.dumps(record),
                }
            )

    print(f"\n📦 Total lignes à insérer : {len(records_to_insert)}")

    if records_to_insert:
        schema = [
            bigquery.SchemaField("surrogate_key", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("hash", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("inserted_at", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("payload", "STRING", mode="NULLABLE"),
        ]

        table = bigquery.Table(TABLE_ID, schema=schema)
        client.create_table(table, exists_ok=True)

        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # Écrase la table brute propre
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        )

        job = client.load_table_from_json(
            records_to_insert, TABLE_ID, job_config=job_config
        )
        job.result()
        print("✅ Ingestion réussie dans BigQuery !")


if __name__ == "__main__":
    ingest_data()