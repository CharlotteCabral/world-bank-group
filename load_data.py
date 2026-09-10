import datetime
import hashlib
import json
import time
from typing import Any, Dict, List

from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
from google.cloud import bigquery
import requests

# ------------------------------------------------------------------------------
# CONSTANTES (Conventions Clean Code & Valeurs isolées)
# ------------------------------------------------------------------------------
DATASET_ID = "world_bank_raw"
TABLE_NAME = "raw_data"
API_BASE_URL = "https://api.worldbank.org/v2/country/all/indicator"
HTTP_TIMEOUT = (10, 30)
API_PAGE_LIMIT = 500
API_RATE_LIMIT_DELAY = 0.3
MAX_RETRIES = 5

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


# ------------------------------------------------------------------------------
# FONCTIONS UTILITAIRES DE TRANSFORMATION / HASH
# ------------------------------------------------------------------------------
def generer_hash_sha256(chaine: str) -> str:
    """Calcule l'empreinte SHA256 d'une chaîne de caractères."""
    return hashlib.sha256(chaine.encode("utf-8")).hexdigest()


def generer_cle_substitution(enregistrement: Dict[str, Any]) -> str:
    """Génère la clé de substitution (surrogate_key) pour un enregistrement."""
    pays = enregistrement.get("countryiso3code") or ""
    date = enregistrement.get("date") or ""
    indicateur_obj = enregistrement.get("indicator") or {}
    indicateur_id = indicateur_obj.get("id") or ""

    cle_brute = f"{pays}_{date}_{indicateur_id}"
    return generer_hash_sha256(cle_brute)


def preparer_enregistrement_pour_insertion(
    enregistrement: Dict[str, Any], horodatage_iso: str
) -> Dict[str, Any]:
    """Transforme un enregistrement brut de l'API en dictionnaire prêt pour BigQuery."""
    payload_json = json.dumps(enregistrement, sort_keys=True)
    hash_payload = generer_hash_sha256(payload_json)
    cle_substitution = generer_cle_substitution(enregistrement)

    return {
        "surrogate_key": cle_substitution,
        "hash": hash_payload,
        "inserted_at": horodatage_iso,
        "payload": json.dumps(enregistrement),
    }


# ------------------------------------------------------------------------------
# MODULE INGESTION API (Extraction)
# ------------------------------------------------------------------------------
def extraire_donnees_indicateur(code_indicateur: str) -> List[Dict[str, Any]]:
    """Récupère l'ensemble des pages de données pour un indicateur donné via l'API World Bank."""
    enregistrements = []
    page = 1
    total_pages = 1

    while page <= total_pages:
        url = f"{API_BASE_URL}/{code_indicateur}"
        parametres = {
            "format": "json",
            "per_page": API_PAGE_LIMIT,
            "page": page,
        }

        try:
            reponse = requests.get(
                url, params=parametres, timeout=HTTP_TIMEOUT
            )
            if reponse.status_code != 200:
                print(
                    f"❌ {code_indicateur} (Page {page}) : HTTP {reponse.status_code}"
                )
                break

            donnees = reponse.json()
            if (
                not isinstance(donnees, list)
                or len(donnees) < 2
                or not isinstance(donnees[0], dict)
            ):
                print(
                    f"⚠️ {code_indicateur} (Page {page}) : Pas de données renvoyées"
                )
                break

            total_pages = donnees[0].get("pages", 1)
            enregistrements_bruts = donnees[1]

            if enregistrements_bruts:
                enregistrements.extend(enregistrements_bruts)

            page += 1
            time.sleep(API_RATE_LIMIT_DELAY)

        except (requests.RequestException, json.JSONDecodeError) as erreur:
            print(f"❌ {code_indicateur} (Page {page}) : Erreur -> {erreur}")
            break

    return enregistrements


# ------------------------------------------------------------------------------
# MODULE CHARGEMENT BIGQUERY (Chargement)
# ------------------------------------------------------------------------------
def charger_donnees_dans_bigquery(
    client: bigquery.Client,
    chemin_table: str,
    enregistrements: List[Dict[str, Any]],
    mode_ecriture: str = bigquery.WriteDisposition.WRITE_APPEND,
) -> None:
    """Crée la table au besoin et y déverse la liste d'enregistrements préparés."""
    schema = [
        bigquery.SchemaField("surrogate_key", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("hash", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("inserted_at", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("payload", "STRING", mode="NULLABLE"),
    ]

    table = bigquery.Table(chemin_table, schema=schema)
    client.create_table(table, exists_ok=True)

    configuration_job = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=mode_ecriture,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    job = client.load_table_from_json(
        enregistrements, chemin_table, job_config=configuration_job
    )
    job.result()
    print("✅ Ingestion réussie dans BigQuery !")


# ------------------------------------------------------------------------------
# ORCHESTRATEUR PRINCIPAL
# ------------------------------------------------------------------------------
def ingest_data() -> None:
    """Orchestre le pipeline ELT sans effacer les données existantes (Mode Append)."""
    load_dotenv()
    client = bigquery.Client()
    chemin_table = f"{client.project}.{DATASET_ID}.{TABLE_NAME}"
    maintenant_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    total_lignes_inserees = 0

    for code_indicateur in INDICATORS:
        print(f"🔄 Récupération : {code_indicateur}...")
        enregistrements_bruts = extraire_donnees_indicateur(code_indicateur)

        if not enregistrements_bruts:
            print(f"  ⚠️ 0 ligne pour {code_indicateur}, passage au suivant.")
            continue

        lignes_a_inserer = [
            preparer_enregistrement_pour_insertion(rec, maintenant_iso)
            for rec in enregistrements_bruts
        ]

        charger_donnees_dans_bigquery(
            client,
            chemin_table,
            lignes_a_inserer,
            mode_ecriture=bigquery.WriteDisposition.WRITE_APPEND,
        )
        total_lignes_inserees += len(lignes_a_inserer)
        print(f"  ✅ {len(lignes_a_inserer)} lignes ajoutées pour {code_indicateur}.")

    print(
        f"\n🎉 Ingestion terminée ! {total_lignes_inserees} nouvelles lignes ajoutées."
    )


if __name__ == "__main__":
    ingest_data()