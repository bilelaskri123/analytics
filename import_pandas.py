import pandas as pd
from python_calamine import CalamineWorkbook
import os
from insert_db import insertInDB

# ── 1. Load the Excel file ───────────────────────────────────────────────────
file_path = r"export_axia/downloads/ListeVersements.xlsx"

# 1. Load the workbook using raw calamine
workbook = CalamineWorkbook.from_path(file_path)

# 2. Extract rows from the first sheet
sheet_name = workbook.sheet_names[0]
raw_rows = workbook.get_sheet_by_name(sheet_name).to_python()

# 3. Convert the raw text rows into a Pandas DataFrame
df = pd.DataFrame(raw_rows[1:], columns=raw_rows[0])

# ── 2. Cast column types ─────────────────────────────────────────────────────
df["Statut"]                      = df["Statut"].astype(str)
df["N° Bordereau"]                = df["N° Bordereau"].astype(str)
df["Intitulé agence"]             = df["Intitulé agence"].astype(str)
df["Région"]                      = df["Région"].astype(str)
df["Responsable régional"]        = df["Responsable régional"].astype(str)
df["Users"]                       = df["Users"].astype(str)
df["Détails Chéques"]             = df["Détails Chéques"].astype(str)
df["Banque/Code Banque"]          = df["Banque/Code Banque"].astype(str)
df["Nombre de jours de blocage"]  = pd.to_numeric(df["Nombre de jours de blocage"], errors="coerce").astype("Int64")
df["Date de création"]            = pd.to_datetime(df["Date de création"], format='%d/%m/%Y', errors='coerce')
df["Date dernière modification"]  = pd.to_datetime(df["Date dernière modification"], format='%d/%m/%Y %H:%M:%S', errors='coerce')
df["Total Règlements"]            = df["Total Règlements"].astype(str).str.replace(',', '.')
df["Total des factures à verser"] = df["Total des factures à verser"].astype(str).str.replace(',', '.')
df["Commentaires"]                = df["Commentaires"].astype(str)
df["Créateur"]                    = df["Créateur"].astype(str)
df["Modificateur"]                = df["Modificateur"].astype(str)
df["Durée de période facturée"]   = pd.to_numeric(df["Durée de période facturée"], errors="coerce").astype("Int64")
df["Délai de traitement"]         = pd.to_numeric(df["Délai de traitement"], errors="coerce").astype("Int64")

# ── 3. Montant Bordereau  (was "Personnalisé") ───────────────────────────────
# If the raw string contains a comma → keep as-is; 
# if numeric 10 000–1 000 000 → divide by 1000; else keep numeric value.
def calc_montant_bordereau(raw):
    s = str(raw)
    
    new_raw = ''
    if s.find('\xa0') != -1:
        new_raw = s.replace('\xa0', '')
    else:
        new_raw = s;
    
    try:
        val = float(new_raw)
    except (ValueError, TypeError):
            print(f"could not convert {new_raw} to a float")
            return 0
    if 10_000 <= val <= 1_000_000:
            return val / 1_000
    return val

df["Montant Bordereau"] = df["Total Règlements"].apply(calc_montant_bordereau)

# ── 4. Plafond AG  (was "Personnalisé.1") ────────────────────────────────────
def calc_plafond_ag(val):
    val_string = str(val)
    val_string = val_string.replace('\xa0', '').replace(',', '.')
    v = 0
    try:
        v = float(val_string)
    except (ValueError, TypeError):
        return val
    if v > 100_001:
        return v / 1_000
    else:
        return v

df["Plafond AG"] = df["Plafond"].apply(calc_plafond_ag)

# ── 5. Factures a verser  (was "Personnalisé.2") ─────────────────────────────
def calc_factures(raw):
    s = str(raw).replace('\xa0', '')
    # if "," in s:
    #     return raw
    try:
        val = float(s)
    except (ValueError, TypeError):
        print(s, ValueError, TypeError)
        return None
    if 10000 <= val <= 1000000:
        return val / 1000
    return val

df["Factures a verser"] = df["Total des factures à verser"].apply(calc_factures)

# ── 6. Région Nettoyée ───────────────────────────────────────────────────────
def clean_region(val):
    v = str(val)
    if v.startswith("REG"):
        v = v[3:]
    v = v.replace("SFX",        "SFAX")
    v = v.replace("TUN2",       "TUN 2")
    v = v.replace("TUN",        "TUNIS")
    v = v.replace("SIDIBOUZID", "SIDI BOUZID")
    v = v.replace("BENAROUS",   "BEN AROUS")
    v = v.replace("ARIANA2",    "ARIANA 2")
    v = v.replace("MANOUBA2",   "MANOUBA 2")
    v = v.replace("ION-SAHEL",  "SOUSSE")
    return v

df["Région Nettoyée"] = df["Région"].apply(clean_region)

# ── 7. Etat ──────────────────────────────────────────────────────────────────
def extract_etat(texte):
    texte = str(texte)
    marker = "Etat :"
    start = texte.find(marker)
    if start == -1:
        return ""
    start += len(marker)
    end = texte.find("Groupe :", start)
    if end == -1 or end <= start:
        return ""
    return texte[start:end].strip()

df["Etat"] = df["Users"].apply(extract_etat)

# ── 8. Groupe ────────────────────────────────────────────────────────────────
def extract_groupe(texte):
    texte = str(texte)
    parts = texte.split("Groupe :")
    if len(parts) <= 1:
        return ""
    val = parts[1][0:30].strip()
    if val.startswith("PVI"):
        return "ACTIVE"
    if val.startswith("Blocage Paiement & Livraison"):
        return "BLOCAGE PAIEMENT"
    return val

df["Groupe"] = df["Users"].apply(extract_groupe)

# glpat-lszhB_nshfwRGAiIODGhRmM6MQpvOjEKdTo0eWwzcg8.01.1700etxl4glpat-lszhB_nshfwRGAiIODGhRmM6MQpvOjEKdTo0eWwzcg8.01.1700etxl4

# ── 9. Banque ────────────────────────────────────────────────────────────────
def extract_banque(code):
    try:
        code = str(code)
    except Exception:
        return ""
    if "B50" in code:
        return "STB"
    if "B51" in code:
        return "BNA"
    if "B40" in code:
        return "ATTIJARI"
    if "P02" in code:
        return "CCP"
    return ""

df["Banque"] = df["Banque/Code Banque"].apply(extract_banque)


# ── 10. Drop original columns replaced by cleaned versions ───────────────────
df = df.drop(columns=[
    "Total Règlements",           
    "Total des factures à verser",
    "Plafond",
    "Users",
    "Région",                   
    "Banque/Code Banque",         
])


# ── 2. rename columns ─────────────────────────────────────────────────────
df.rename(columns={'Statut': 'statut'}, inplace=True)
df.rename(columns={"N° Bordereau": "numero_bordereau"}, inplace=True)
df.rename(columns={"Intitulé agence": "intitule_agence"}, inplace=True)
df.rename(columns={"Responsable régional": "responsable_regional"}, inplace=True)
df.rename(columns={"Users": "users"}, inplace=True)
df.rename(columns={"Région Nettoyée": "region"}, inplace=True)
df.rename(columns={"Etat": "etat"}, inplace=True)
df.rename(columns={"Groupe": "groupe"}, inplace=True)
df.rename(columns={"factures a verser": "factures_a_verser"}, inplace=True)
df.rename(columns={"Banque": "banque"}, inplace=True)
df.rename(columns={"Détails Chéques": "details_cheques"}, inplace=True)
df.rename(columns={"Nombre de jours de blocage": "nombre_jours_blocage"}, inplace=True)
df.rename(columns={"Date de création": "date_creation"}, inplace=True)
df.rename(columns={"Date dernière modification": "date_derniere_modification"}, inplace=True)
df.rename(columns={"Commentaires": "commentaires"}, inplace=True)
df.rename(columns={"Créateur": "createur"}, inplace=True)
df.rename(columns={"Modificateur": "modificateur"}, inplace=True)
df.rename(columns={"Durée de période facturée": "duree_periode_facturee"}, inplace=True)
df.rename(columns={"Délai de traitement": "delai_traitement"}, inplace=True)
df.rename(columns={"Montant Bordereau": "montant_bordereau"}, inplace=True)
df.rename(columns={"Plafond AG": "plafond_ag"}, inplace=True)
df.rename(columns={"Factures a verser": "factures_a_verser"}, inplace=True)
df.rename(columns={"Action": "action"}, inplace=True)

insertInDB(df)
# os.remove(file_path)