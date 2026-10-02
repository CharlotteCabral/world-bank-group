import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# URL de base de l'API de la Banque Mondiale
API_BASE_URL = "https://api.worldbank.org/v2/country/all/indicator"

# Dictionnaire associant tes noms de variables aux codes officiels de la Banque Mondiale
# (Adapte les codes à gauche si besoin selon ceux que tu utilises dans ton load_data.py)
INDICATORS_MAP = {
    "SL.UEM.TOTL.ZS": "chomage",
    "EN.GHG.CO2.PC.CE.AR5": "co2_par_habitant",
    "SP.DYN.LE00.IN": "esperance_vie",
    "FP.CPI.TOTL.ZG": "inflation",
    "NY.GDP.MKTP.CD": "pib",
    "SE.SEC.ENRL.TC.ZS": "scolarisation_secondaire"
}

all_data = []

print("Récupération des données depuis l'API de la Banque Mondiale...")

# Boucle pour interroger l'API pour chaque indicateur
for code_api, nom_colonne in INDICATORS_MAP.items():
    url = f"{API_BASE_URL}/{code_api}?format=json&per_page=2000"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if len(data) > 1 and data[1]:
            for entry in data[1]:
                country = entry.get('country', {}).get('value')
                year = entry.get('date')
                value = entry.get('value')
                
                if country and year and value is not None:
                    all_data.append({
                        'country': country,
                        'year': year,
                        'indicateur': nom_colonne,
                        'value': value
                    })

# Transformation en DataFrame Pandas
df_raw = pd.DataFrame(all_data)

if df_raw.empty:
    print("Erreur : Aucune donnée n'a été récupérée de l'API.")
else:
    # On pivote le tableau pour avoir chaque indicateur dans sa propre colonne
    df_pivot = df_raw.pivot_table(
        index=['country', 'year'], 
        columns='indicateur', 
        values='value'
    ).reset_index()

    df_pivot.columns.name = None

    # Sélection uniquement de tes 6 colonnes d'intérêt
    colonnes_interet = list(INDICATORS_MAP.values())
    numeric_df = df_pivot[colonnes_interet].select_dtypes(include=['float64', 'int64'])

    # Calcul de la matrice de corrélation
    corr_matrix = numeric_df.corr()

    # Création et sauvegarde de la Heatmap
    plt.figure(figsize=(9, 7))
    sns.heatmap(
        corr_matrix, 
        annot=True, 
        cmap="coolwarm", 
        fmt=".2f", 
        vmin=-1, 
        vmax=1,
        linewidths=0.5
    )
    
    plt.title("Matrice de corrélation - Indicateurs Socio-économiques & CO2", fontsize=12, pad=15)
    plt.tight_layout()

    # Sauvegarde automatique de l'image
    plt.savefig('matrice_correlation.png', dpi=300)
    print("Succès ! Image 'matrice_correlation.png' générée et prête pour Power BI.")
    
    plt.show()