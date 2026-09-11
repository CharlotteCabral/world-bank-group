import datetime
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Set

from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
from google.cloud import bigquery
import requests

# ------------------------------------------------------------------------------
# CONFIGURATION DU LOGGING
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# CONSTANTES
# ------------------------------------------------------------------------------
DATASET_ID = "world_bank_raw"
TABLE_NAME = "raw_data"
API_BASE_URL = "https://api.worldbank.org/v2/country/all/indicator"
HTTP_TIMEOUT = (10, 30)
API_PAGE_LIMIT = 500
API_RATE_LIMIT_DELAY = 0.3

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
# FONCTIONS UTILITAIRES DE HASH ET TRANSFORMATION
# ------------------------------------------------------------------------------
def generer_hash_sha256(chaine: str) -> str:
    """Calcule l'empreinte SHA256 d'une chaîne de caractères."""
    return hashlib.sha256(chaine.encode("utf-8")).hexdigest()


def calculer_hash_brut(enregistrement: Dict[str, Any]) -> str:
    """Calcule le hash sur les données brutes de l'API (sans métadonnées de pipeline)[cite: 3]."""
    payload_str = json.dumps(enregistrement, sort_keys=True, ensure_ascii=False)
    return generer_hash_sha256(payload_str)


def generer_cle_substitution(enregistrement: Dict[str, Any]) -> str:
    """Génère la clé de substitution (surrogate_key) pour un enregistrement."""
    pays = enregistrement.get("countryiso3code") or ""
    date = enregistrement.get("date") or ""
    indicateur_obj = enregistrement.get("indicator") or {}
    indicateur_id = indicateur_obj.get("id") or ""

    cle_brute = f"{pays}_{date}_{indicateur_id}"
    return generer_hash_sha256(cle_brute)


def preparer_enregistrement_pour_insertion(
    enregistrement: Dict[str, Any], horodatage_iso: str, batch_id: str
) -> Dict[str, Any]:
    """Prépare l'enregistrement brut en y ajoutant le hash, la clé et les métadonnées[cite: 2, 3]."""
    # 1. Le hash est calculé UNIQUEMENT sur la donnée brute[cite: 3]
    hash_payload = calculer_hash_brut(enregistrement)
    cle_substitution = generer_cle_substitution(enregistrement)

    # 2. On enrichit l'objet avec la traçabilité (batch_id)[cite: 2]
    enregistrement_enrichi = dict(enregistrement)
    enregistrement_enrichi["batch_id"] = batch_id

    return {
        "surrogate_key": cle_substitution,
        "hash": hash_payload,
        "inserted_at": horodatage_iso,
        "payload": json.dumps(enregistrement_enrichi),
    }


def get_existing_hashes(client: bigquery.Client, chemin_table: str) -> Set[str]:
    """Récupère l'ensemble des hash déjà présents dans la table pour le filtrage."""
    try:
        client.get_table(chemin_table)
        query = f"SELECT DISTINCT `hash` FROM `{chemin_table}`"
        return {row["hash"] for row in client.query(query).result()}
    except NotFound:
        return set()


# ------------------------------------------------------------------------------
# MODULE EXTRACTION (API)
# ------------------------------------------------------------------------------
def extraire_donnees_indicateur(code_indicateur: str) -> List[Dict[str, Any]]:
    """Récupère l'ensemble des pages de données pour un indicateur via l'API."""
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
            reponse = requests.get(url, params=parametres, timeout=HTTP_TIMEOUT)
            reponse.raise_for_status()

            donnees = reponse.json()
            if (
                not isinstance(donnees, list)
                or len(donnees) < 2
                or not isinstance(donnees[0], dict)
            ):
                logger.warning(f"⚠️ {code_indicateur} (Page {page}) : Format invalide ou vide.")
                break

            total_pages = donnees[0].get("pages", 1)
            enregistrements_bruts = donnees[1]

            if enregistrements_bruts:
                enregistrements.extend(enregistrements_bruts)

            page += 1
            time.sleep(API_RATE_LIMIT_DELAY)

        except requests.exceptions.RequestException as erreur:
            logger.error(f"❌ Erreur réseau pour {code_indicateur} (Page {page}) : {erreur}")
            break
        except (json.JSONDecodeError, KeyError):
            logger.exception(f"❌ Erreur de traitement pour {code_indicateur} (Page {page})")
            break

    return enregistrements


# ------------------------------------------------------------------------------
# MODULE CHARGEMENT BIGQUERY & ROLLBACK
# ------------------------------------------------------------------------------
def charger_donnees_dans_bigquery(
    client: bigquery.Client,
    chemin_table: str,
    enregistrements: List[Dict[str, Any]],
) -> None:
    """Crée la table au besoin et y déverse les enregistrements préparés."""
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
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    job = client.load_table_from_json(
        enregistrements, chemin_table, job_config=configuration_job
    )
    job.result()


def annuler_le_lot(client: bigquery.Client, chemin_table: str, batch_id: str) -> None:
    """Supprime toutes les lignes insérées par cette exécution en cas d'échec (Rollback)[cite: 2]."""
    requete = f"DELETE FROM `{chemin_table}` WHERE batch_id = @batch_id"
    config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("batch_id", "STRING", batch_id)
        ]
    )
    client.query(requete, job_config=config).result()
    logger.warning(f"🗑️ Lot {batch_id} supprimé.")


# ------------------------------------------------------------------------------
# ORCHESTRATEUR PRINCIPAL
# ------------------------------------------------------------------------------
def ingest_data() -> None:
    """Orchestre le pipeline ELT avec filtrage anti-doublons et rollback[cite: 2, 3]."""
    load_dotenv()
    client = bigquery.Client()
    chemin_table = f"{client.project}.{DATASET_ID}.{TABLE_NAME}"
    
    maintenant_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    batch_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    logger.info(f"🚀 Début de l'ingestion des données, lot {batch_id}")

    total_lignes_inserees = 0

    try:
        # Récupération des hash déjà en base pour éviter les doublons[cite: 3]
        hashes_existants = get_existing_hashes(client, chemin_table)

        for code_indicateur in INDICATORS:
            logger.info(f"🔄 Récupération de l'indicateur : {code_indicateur}")
            enregistrements_bruts = extraire_donnees_indicateur(code_indicateur)

            if not enregistrements_bruts:
                logger.warning(f"⚠️ 0 ligne récupérée pour {code_indicateur}, passage au suivant.")
                continue

            # Préparation des lignes
            lignes_a_inserer = [
                preparer_enregistrement_pour_insertion(rec, maintenant_iso, batch_id)
                for rec in enregistrements_bruts
            ]

            # Filtrage : on ne garde que les lignes dont le hash n'existe pas encore[cite: 3]
            lignes_neuves = [
                l for l in lignes_a_inserer if l["hash"] not in hashes_existants
            ]

            if not lignes_neuves:
                logger.info(f"ℹ️ Aucune nouvelle ligne pour {code_indicateur} : tout est déjà en base[cite: 3].")
                continue

            # Chargement des nouvelles lignes uniquement[cite: 3]
            charger_donnees_dans_bigquery(client, chemin_table, lignes_neuves)

            # Mise à jour de l'ensemble local pour éviter les doublons si l'indicateur se répétait
            for l in lignes_neuves:
                hashes_existants.add(l["hash"])

            total_lignes_inserees += len(lignes_neuves)
            logger.info(f"✅ {len(lignes_neuves)} nouvelles lignes insérées pour {code_indicateur}.")

        logger.info(f"🎉 Ingestion terminée avec succès ! Total de nouvelles lignes ajoutées : {total_lignes_inserees}")

    except Exception:
        logger.error(f"❌ Ingestion interrompue, annulation du lot {batch_id}")
        annuler_le_lot(client, chemin_table, batch_id)
        logger.error(f"🔄 Rollback effectué : le lot {batch_id} n'existe plus[cite: 2].")
        raise  # Obligatoire pour faire échouer le pipeline proprement[cite: 2]


if __name__ == "__main__":
    ingest_data()