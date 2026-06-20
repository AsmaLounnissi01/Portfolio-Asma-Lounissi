from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "bank" / "bank-full.csv"
OUT_DIR = ROOT / "data" / "processed"


MONTH_ORDER = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

MONTH_FR = {
    "jan": "janvier",
    "feb": "fevrier",
    "mar": "mars",
    "apr": "avril",
    "may": "mai",
    "jun": "juin",
    "jul": "juillet",
    "aug": "aout",
    "sep": "septembre",
    "oct": "octobre",
    "nov": "novembre",
    "dec": "decembre",
}

JOB_FR = {
    "admin.": "Administratif",
    "blue-collar": "Ouvrier",
    "entrepreneur": "Entrepreneur",
    "housemaid": "Employe a domicile",
    "management": "Management",
    "retired": "Retraite",
    "self-employed": "Independant",
    "services": "Services",
    "student": "Etudiant",
    "technician": "Technicien",
    "unemployed": "Sans emploi",
    "unknown": "Inconnu",
}

MARITAL_FR = {
    "divorced": "Divorce",
    "married": "Marie",
    "single": "Celibataire",
}

EDUCATION_FR = {
    "primary": "Primaire",
    "secondary": "Secondaire",
    "tertiary": "Superieur",
    "unknown": "Inconnu",
}

CONTACT_FR = {
    "cellular": "Mobile",
    "telephone": "Telephone",
    "unknown": "Inconnu",
}

POUTCOME_FR = {
    "failure": "Echec",
    "other": "Autre",
    "success": "Succes",
    "unknown": "Inconnu",
}

AGENCES = [
    ("AG001", "Paris Opera", "Ile-de-France", "Paris"),
    ("AG002", "Lyon Part-Dieu", "Auvergne-Rhone-Alpes", "Lyon"),
    ("AG003", "Marseille Prado", "Provence-Alpes-Cote d'Azur", "Marseille"),
    ("AG004", "Lille Centre", "Hauts-de-France", "Lille"),
    ("AG005", "Bordeaux Meriadeck", "Nouvelle-Aquitaine", "Bordeaux"),
    ("AG006", "Nantes Commerce", "Pays de la Loire", "Nantes"),
    ("AG007", "Toulouse Capitole", "Occitanie", "Toulouse"),
    ("AG008", "Strasbourg Etoile", "Grand Est", "Strasbourg"),
]


def segment_age(age: int) -> str:
    if age < 30:
        return "18-29"
    if age < 40:
        return "30-39"
    if age < 50:
        return "40-49"
    if age < 60:
        return "50-59"
    return "60+"


def segment_solde(balance: int) -> str:
    if balance < 0:
        return "Solde negatif"
    if balance < 500:
        return "0-499"
    if balance < 2000:
        return "500-1999"
    if balance < 5000:
        return "2000-4999"
    return "5000+"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RAW_FILE, sep=";")
    df = df.reset_index().rename(columns={"index": "contact_id"})
    df["contact_id"] = df["contact_id"] + 1
    df["client_id"] = df["contact_id"].map(lambda x: f"CL{x:06d}")

    df["age_segment"] = df["age"].map(segment_age)
    df["balance_segment"] = df["balance"].map(segment_solde)
    df["subscribed"] = (df["y"] == "yes").astype(int)
    df["has_housing_loan"] = (df["housing"] == "yes").astype(int)
    df["has_personal_loan"] = (df["loan"] == "yes").astype(int)
    df["has_default"] = (df["default"] == "yes").astype(int)
    df["contact_duration_min"] = (df["duration"] / 60).round(2)
    df["month_num"] = df["month"].map(MONTH_ORDER)
    df["month_name"] = df["month"].map(MONTH_FR)
    df["campaign_intensity"] = pd.cut(
        df["campaign"],
        bins=[0, 1, 3, 6, 100],
        labels=["1 contact", "2-3 contacts", "4-6 contacts", "7+ contacts"],
        include_lowest=True,
    )

    df["job_fr"] = df["job"].map(JOB_FR)
    df["marital_fr"] = df["marital"].map(MARITAL_FR)
    df["education_fr"] = df["education"].map(EDUCATION_FR)
    df["contact_fr"] = df["contact"].map(CONTACT_FR)
    df["previous_outcome_fr"] = df["poutcome"].map(POUTCOME_FR)

    agency_ids = [a[0] for a in AGENCES]
    df["agency_id"] = df["contact_id"].map(lambda x: agency_ids[x % len(agency_ids)])

    contacts = df[
        [
            "contact_id",
            "client_id",
            "agency_id",
            "age",
            "age_segment",
            "job_fr",
            "marital_fr",
            "education_fr",
            "balance",
            "balance_segment",
            "has_default",
            "has_housing_loan",
            "has_personal_loan",
            "contact_fr",
            "day",
            "month_num",
            "month_name",
            "duration",
            "contact_duration_min",
            "campaign",
            "campaign_intensity",
            "pdays",
            "previous",
            "previous_outcome_fr",
            "subscribed",
        ]
    ].copy()

    agences = pd.DataFrame(AGENCES, columns=["agency_id", "agency_name", "region", "city"])

    produits = pd.DataFrame(
        [
            ("PR001", "Depot a terme", "Epargne", "Produit cible de la campagne marketing"),
            ("PR002", "Credit immobilier", "Credit", "Indicateur issu de la variable housing"),
            ("PR003", "Credit personnel", "Credit", "Indicateur issu de la variable loan"),
        ],
        columns=["product_id", "product_name", "product_family", "description"],
    )

    quality = pd.DataFrame(
        [
            ("job_fr", int((contacts["job_fr"] == "Inconnu").sum()), len(contacts)),
            ("education_fr", int((contacts["education_fr"] == "Inconnu").sum()), len(contacts)),
            ("contact_fr", int((contacts["contact_fr"] == "Inconnu").sum()), len(contacts)),
            ("previous_outcome_fr", int((contacts["previous_outcome_fr"] == "Inconnu").sum()), len(contacts)),
        ],
        columns=["field_name", "unknown_count", "row_count"],
    )
    quality["unknown_rate"] = (quality["unknown_count"] / quality["row_count"]).round(4)

    contacts.to_csv(OUT_DIR / "contacts_campagne_bancaire.csv", index=False, encoding="utf-8-sig")
    agences.to_csv(OUT_DIR / "agences.csv", index=False, encoding="utf-8-sig")
    produits.to_csv(OUT_DIR / "produits.csv", index=False, encoding="utf-8-sig")
    quality.to_csv(OUT_DIR / "qualite_donnees.csv", index=False, encoding="utf-8-sig")

    summary = {
        "lignes_contacts": len(contacts),
        "clients_souscripteurs": int(contacts["subscribed"].sum()),
        "taux_conversion": round(float(contacts["subscribed"].mean()), 4),
        "solde_moyen": round(float(contacts["balance"].mean()), 2),
        "duree_contact_moyenne_min": round(float(contacts["contact_duration_min"].mean()), 2),
    }
    pd.DataFrame(
        [{"metric": key, "value": value} for key, value in summary.items()]
    ).to_csv(OUT_DIR / "resume_kpi.csv", index=False, encoding="utf-8-sig")

    print("Fichiers generes dans", OUT_DIR)
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
