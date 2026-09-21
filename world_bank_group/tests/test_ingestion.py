# tests/test_ingestion.py
from load_data import calculer_hash_brut

def test_meme_ligne_meme_empreinte():
    """Vérifie qu'une même ligne donne toujours la même empreinte."""
    ligne = {"countryiso3code": "FRA", "date": "2023", "value": 100}
    assert calculer_hash_brut(ligne) == calculer_hash_brut(ligne)

def test_lignes_differentes_empreintes_differentes():
    """Vérifie que deux lignes différentes donnent des empreintes différentes."""
    ligne_a = {"countryiso3code": "FRA", "date": "2023", "value": 100}
    ligne_b = {"countryiso3code": "DEU", "date": "2023", "value": 100}
    assert calculer_hash_brut(ligne_a) != calculer_hash_brut(ligne_b)