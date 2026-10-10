"""Génère le jeu de données fictif de la banque de détail « Banque Aurore ».

Toutes les données sont simulées (aucune donnée réelle) : agences, conseillers,
clients, produits, opportunités commerciales 2024-2025 et objectifs mensuels.
Le script est déterministe (graine fixe) pour que les résultats soient reproductibles.

Usage : python generer_donnees.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(2025)
OUT = Path(__file__).resolve().parents[1] / "data"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- référentiels
REGIONS = {
    "Île-de-France": ["Paris Bastille", "Paris La Défense", "Versailles", "Créteil"],
    "Auvergne-Rhône-Alpes": ["Lyon Part-Dieu", "Grenoble", "Annecy"],
    "Hauts-de-France": ["Lille Centre", "Amiens", "Roubaix"],
    "Nouvelle-Aquitaine": ["Bordeaux Chartrons", "Pau"],
}
# potentiel commercial de chaque agence (multiplicateur d'activité)
POTENTIEL = {
    "Paris Bastille": 1.35, "Paris La Défense": 1.5, "Versailles": 1.1, "Créteil": 0.9,
    "Lyon Part-Dieu": 1.25, "Grenoble": 0.95, "Annecy": 0.8,
    "Lille Centre": 1.1, "Amiens": 0.7, "Roubaix": 0.75,
    "Bordeaux Chartrons": 1.15, "Pau": 0.65,
}
# efficacité commerciale propre à l'agence (impacte la transformation)
EFFICACITE = {
    "Paris Bastille": 1.05, "Paris La Défense": 0.97, "Versailles": 1.1, "Créteil": 0.88,
    "Lyon Part-Dieu": 1.08, "Grenoble": 1.0, "Annecy": 1.12,
    "Lille Centre": 0.95, "Amiens": 0.9, "Roubaix": 0.82,
    "Bordeaux Chartrons": 1.06, "Pau": 1.0,
}

agences = []
for region, villes in REGIONS.items():
    for v in villes:
        agences.append({"id_agence": f"AG{len(agences) + 1:02d}", "agence": v, "region": region})
agences = pd.DataFrame(agences)

PRODUITS = pd.DataFrame([
    # id, produit, famille, montant min, montant max (loi log-normale bornée), taux PNB, poids, transfo de base
    ("P01", "Crédit immobilier", "Crédit", 90_000, 420_000, 0.011, 0.08, 0.30),
    ("P02", "Crédit consommation", "Crédit", 3_000, 35_000, 0.045, 0.13, 0.38),
    ("P03", "Livret d'épargne", "Épargne", 500, 20_000, 0.006, 0.17, 0.62),
    ("P04", "Assurance vie", "Épargne", 5_000, 120_000, 0.010, 0.10, 0.33),
    ("P05", "PEA", "Épargne", 2_000, 60_000, 0.008, 0.05, 0.28),
    ("P06", "Assurance habitation", "Assurance", 180, 650, 0.35, 0.14, 0.45),
    ("P07", "Prévoyance", "Assurance", 300, 1_600, 0.40, 0.08, 0.27),
    ("P08", "Carte premium", "Services", 140, 320, 0.90, 0.15, 0.50),
    ("P09", "Banque à distance pro", "Services", 360, 1_200, 0.85, 0.10, 0.36),
], columns=["id_produit", "produit", "famille", "montant_min", "montant_max", "taux_pnb", "poids", "transfo_base"])

SEGMENTS = {
    # segment: (part des clients, produits détenus au départ, risque d'attrition de base)
    "Jeunes actifs": (0.27, 1.3, 0.11),
    "Familles": (0.30, 2.4, 0.06),
    "Seniors": (0.20, 2.1, 0.045),
    "Patrimonial": (0.11, 3.4, 0.035),
    "Professionnels": (0.12, 2.2, 0.07),
}
AFFINITE = {  # multiplicateur de probabilité de demande d'un produit selon le segment
    "Jeunes actifs": {"P01": 0.7, "P02": 1.6, "P03": 1.5, "P04": 0.4, "P05": 0.7, "P06": 1.3, "P07": 0.5, "P08": 1.2, "P09": 0.1},
    "Familles": {"P01": 1.6, "P02": 1.2, "P03": 1.0, "P04": 0.9, "P05": 0.7, "P06": 1.2, "P07": 1.4, "P08": 0.9, "P09": 0.1},
    "Seniors": {"P01": 0.3, "P02": 0.6, "P03": 1.0, "P04": 1.7, "P05": 1.0, "P06": 0.9, "P07": 1.1, "P08": 0.7, "P09": 0.1},
    "Patrimonial": {"P01": 1.1, "P02": 0.3, "P03": 0.6, "P04": 2.2, "P05": 2.0, "P06": 0.8, "P07": 1.0, "P08": 1.4, "P09": 0.2},
    "Professionnels": {"P01": 0.8, "P02": 0.7, "P03": 0.6, "P04": 0.7, "P05": 0.6, "P06": 0.6, "P07": 1.3, "P08": 1.1, "P09": 4.5},
}
CANAUX = {  # canal: (part 2024, part 2025, multiplicateur de transformation)
    "Agence": (0.52, 0.45, 1.18),
    "Téléphone": (0.22, 0.20, 0.82),
    "Visio": (0.11, 0.16, 1.05),
    "En ligne": (0.15, 0.19, 0.58),
}
SAISON = np.array([0.88, 0.95, 1.08, 1.06, 1.04, 1.07, 0.92, 0.62, 1.08, 1.10, 1.06, 0.94])

PRENOMS = ["Camille", "Julien", "Sarah", "Thomas", "Inès", "Nicolas", "Léa", "Karim", "Manon", "Antoine",
           "Chloé", "Mehdi", "Pauline", "Hugo", "Yasmine", "Romain", "Clara", "Lucas", "Amandine", "Samir",
           "Émilie", "Maxime", "Nadia", "Pierre", "Laura", "Bastien", "Sofia", "Kevin", "Margaux", "Adrien",
           "Elise", "Rayan", "Justine", "Florian", "Aïcha", "Vincent", "Marion", "Yanis", "Anaïs", "Quentin",
           "Lina", "Guillaume", "Océane", "Damien", "Salomé", "Alexis", "Jade", "Cédric", "Zoé", "Mathieu"]
NOMS = ["Martin", "Bernard", "Dubois", "Moreau", "Laurent", "Girard", "Roux", "Fournier", "Morel", "Mercier",
        "Blanc", "Guerin", "Boyer", "Garnier", "Chevalier", "Lambert", "Bonnet", "Francois", "Legrand", "Gauthier",
        "Perrin", "Robin", "Clement", "Morin", "Nicolas", "Henry", "Roussel", "Mathieu", "Masson", "Marchand",
        "Duval", "Denis", "Dumont", "Marie", "Lemaire", "Noel", "Meyer", "Dufour", "Meunier", "Brun",
        "Blanchard", "Giraud", "Joly", "Riviere", "Lucas", "Brunet", "Gaillard", "Barbier", "Arnaud", "Martinez"]

# ---------------------------------------------------------------- conseillers
conseillers = []
noms_utilises = set()
for _, ag in agences.iterrows():
    n = int(round(3 + 2.2 * POTENTIEL[ag.agence]))
    for k in range(n):
        while True:
            nom = f"{RNG.choice(PRENOMS)} {RNG.choice(NOMS)}"
            if nom not in noms_utilises:
                noms_utilises.add(nom)
                break
        role = "Conseiller patrimonial" if k == 0 else ("Conseiller professionnels" if k == 1 else "Conseiller particuliers")
        conseillers.append({
            "id_conseiller": f"CO{len(conseillers) + 1:03d}", "conseiller": nom, "id_agence": ag.id_agence,
            "fonction": role, "anciennete_ans": int(RNG.integers(1, 22)),
            "talent": float(np.clip(RNG.normal(1.0, 0.13), 0.7, 1.35)),
        })
conseillers = pd.DataFrame(conseillers)

# ---------------------------------------------------------------- clients
pot = agences.agence.map(POTENTIEL).to_numpy()
N_CLIENTS = 24_000
cli_agence = RNG.choice(agences.id_agence, size=N_CLIENTS, p=pot / pot.sum())
seg_names = list(SEGMENTS)
cli_seg = RNG.choice(seg_names, size=N_CLIENTS, p=[SEGMENTS[s][0] for s in seg_names])
age_par_seg = {"Jeunes actifs": (22, 34), "Familles": (32, 52), "Seniors": (60, 85), "Patrimonial": (40, 75), "Professionnels": (28, 62)}
ages = np.array([RNG.integers(*age_par_seg[s]) for s in cli_seg])
anciennete = np.clip(RNG.gamma(2.2, 4.0, N_CLIENTS), 0, 40).round(1)
anciennete = np.where(cli_seg == "Jeunes actifs", np.minimum(anciennete, ages - 18), anciennete)
detenus = np.array([max(1, RNG.poisson(SEGMENTS[s][1])) for s in cli_seg])  # compte courant inclus
clients = pd.DataFrame({
    "id_client": [f"CL{i + 1:05d}" for i in range(N_CLIENTS)], "id_agence": cli_agence, "segment": cli_seg,
    "age": ages, "anciennete_ans": anciennete, "produits_initiaux": np.minimum(detenus, 6),
})
clients["tranche_age"] = pd.cut(clients.age, [17, 29, 44, 59, 120], labels=["18-29", "30-44", "45-59", "60+"]).astype(str)

# ---------------------------------------------------------------- opportunités commerciales
cons_par_agence = conseillers.groupby("id_agence")
ag_nom = agences.set_index("id_agence").agence
clients_par_agence = {a: g for a, g in clients.groupby("id_agence")}
rows = []
BASE_MENSUELLE = 210  # opportunités par mois pour une agence de potentiel 1 en 2024
for annee, croissance in [(2024, 1.0), (2025, 1.07)]:
    idx_canal = 0 if annee == 2024 else 1
    canaux = list(CANAUX)
    p_canal = np.array([CANAUX[c][idx_canal] for c in canaux])
    for mois in range(1, 13):
        for _, ag in agences.iterrows():
            n = RNG.poisson(BASE_MENSUELLE * POTENTIEL[ag.agence] * SAISON[mois - 1] * croissance)
            cl = clients_par_agence[ag.id_agence].sample(n, replace=True, random_state=int(RNG.integers(1e9)))
            cons = cons_par_agence.get_group(ag.id_agence)
            for _, c in cl.iterrows():
                aff = AFFINITE[c.segment]
                w = PRODUITS.poids.to_numpy() * np.array([aff[p] for p in PRODUITS.id_produit])
                if mois in (3, 4, 5, 6):  # saison immobilière
                    w[0] *= 1.35
                pr = PRODUITS.iloc[RNG.choice(len(PRODUITS), p=w / w.sum())]
                # conseiller : le patrimonial prend les clients patrimoniaux, le pro les professionnels
                if c.segment == "Patrimonial" and RNG.random() < 0.7:
                    co = cons[cons.fonction == "Conseiller patrimonial"].iloc[0]
                elif c.segment == "Professionnels" and RNG.random() < 0.75:
                    co = cons[cons.fonction == "Conseiller professionnels"].iloc[0]
                else:
                    co = cons.iloc[RNG.integers(len(cons))]
                canal = RNG.choice(canaux, p=p_canal)
                p = pr.transfo_base * CANAUX[canal][2] * co.talent * EFFICACITE[ag.agence]
                p *= 1.0 + 0.04 * (annee == 2025)
                signe = RNG.random() < min(p, 0.92)
                lo, hi = np.log(pr.montant_min), np.log(pr.montant_max)
                montant = float(np.exp(RNG.triangular(lo, lo + (hi - lo) * 0.35, hi)))
                if c.segment == "Patrimonial" and pr.famille == "Épargne":
                    montant = min(montant * 2.2, pr.montant_max * 2)
                montant = round(montant, -1 if montant > 1000 else 0)
                jour = int(RNG.integers(1, 29))
                delai = int(np.clip(RNG.gamma(2.0, 6 if pr.famille == "Crédit" else 2.5), 0, 75))
                rows.append((annee, mois, jour, ag.id_agence, co.id_conseiller, c.id_client, pr.id_produit,
                             canal, "Signé" if signe else "Perdu", montant,
                             round(montant * pr.taux_pnb, 2) if signe else 0.0, delai if signe else None))

opp = pd.DataFrame(rows, columns=["annee", "mois", "jour", "id_agence", "id_conseiller", "id_client", "id_produit",
                                  "canal", "statut", "montant", "pnb", "delai_signature_jours"])
opp.insert(0, "date", pd.to_datetime(dict(year=opp.annee, month=opp.mois, day=opp.jour)).dt.strftime("%Y-%m-%d"))
opp = opp.drop(columns=["annee", "mois", "jour"]).sort_values("date").reset_index(drop=True)
opp.insert(0, "id_opportunite", [f"OP{i + 1:06d}" for i in range(len(opp))])
opp["delai_signature_jours"] = opp.delai_signature_jours.astype("Int64")

# ---------------------------------------------------------------- équipement et attrition 2025
signes = opp[opp.statut == "Signé"]
nouveaux = signes.groupby("id_client").id_produit.nunique()
clients["nb_produits"] = (clients.produits_initiaux + clients.id_client.map(nouveaux).fillna(0)).clip(upper=8).astype(int)
risque = clients.segment.map({s: v[2] for s, v in SEGMENTS.items()}).to_numpy()
risque = risque * np.select([clients.nb_produits <= 1, clients.nb_produits == 2, clients.nb_produits == 3],
                            [2.6, 1.5, 0.9], 0.45)
risque *= np.where(clients.anciennete_ans < 2, 1.5, 1.0)
parti = RNG.random(N_CLIENTS) < risque
clients["statut_client"] = np.where(parti, "Parti en 2025", "Actif")
mois_depart = RNG.integers(1, 13, N_CLIENTS)
clients["date_sortie"] = np.where(parti, [f"2025-{m:02d}-15" for m in mois_depart], "")
clients = clients.drop(columns=["produits_initiaux"])

# ---------------------------------------------------------------- objectifs PNB 2025
pnb_2024 = (signes[signes.date < "2025"].assign(mois=lambda d: d.date.str[5:7].astype(int))
            .merge(PRODUITS[["id_produit", "famille"]]).groupby(["id_agence", "mois", "famille"]).pnb.sum())
obj = []
for (ag, mois, fam), v in pnb_2024.items():
    cible = v * RNG.uniform(1.08, 1.16)  # objectif : +8 à +16 % vs N-1
    obj.append({"date": f"2025-{mois:02d}-01", "id_agence": ag, "famille": fam, "objectif_pnb": round(cible, 0)})
objectifs = pd.DataFrame(obj)

# ---------------------------------------------------------------- export
agences.to_csv(OUT / "agences.csv", index=False)
conseillers.drop(columns=["talent"]).to_csv(OUT / "conseillers.csv", index=False)
PRODUITS[["id_produit", "produit", "famille", "taux_pnb"]].to_csv(OUT / "produits.csv", index=False)
clients.to_csv(OUT / "clients.csv", index=False)
opp.to_csv(OUT / "opportunites.csv", index=False)
objectifs.to_csv(OUT / "objectifs.csv", index=False)
print({n: len(d) for n, d in [("agences", agences), ("conseillers", conseillers), ("clients", clients),
                              ("opportunites", opp), ("objectifs", objectifs)]})
