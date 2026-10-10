"""Agrège les données fictives en cubes compacts pour le dashboard web interactif."""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
o = pd.read_csv(D / "opportunites.csv"); p = pd.read_csv(D / "produits.csv"); a = pd.read_csv(D / "agences.csv")
c = pd.read_csv(D / "clients.csv"); ob = pd.read_csv(D / "objectifs.csv"); co = pd.read_csv(D / "conseillers.csv")
o["annee"] = o.date.str[:4].astype(int); o["mois"] = o.date.str[5:7].astype(int)
o["signe"] = (o.statut == "Signé").astype(int)
o["montant_signe"] = o.montant * o.signe
ag = {r.id_agence: i for i, r in a.reset_index().iterrows()}
pr = {r.id_produit: i for i, r in p.reset_index().iterrows()}
canaux = ["Agence", "Téléphone", "Visio", "En ligne"]; cn = {k: i for i, k in enumerate(canaux)}
cube = o.groupby(["annee", "mois", "id_agence", "id_produit", "canal"]).agg(
    n=("signe", "size"), s=("signe", "sum"), pnb=("pnb", "sum"), m=("montant_signe", "sum")).reset_index()
cube_rows = [[int(r.annee) - 2024, int(r.mois), ag[r.id_agence], pr[r.id_produit], cn[r.canal], int(r.n), int(r.s),
              round(r.pnb), round(r.m)] for r in cube.itertuples()]
fam = sorted(p.famille.unique().tolist(), key=["Crédit", "Épargne", "Assurance", "Services"].index)
obj = ob.assign(mois=ob.date.str[5:7].astype(int))
obj_rows = [[int(r.mois), ag[r.id_agence], fam.index(r.famille), round(r.objectif_pnb)] for r in obj.itertuples()]
cons = o.merge(co[["id_conseiller", "conseiller"]]).groupby(["annee", "id_agence", "id_conseiller", "conseiller"]).agg(
    n=("signe", "size"), s=("signe", "sum"), pnb=("pnb", "sum")).reset_index()
cons_rows = [[int(r.annee) - 2024, ag[r.id_agence], r.conseiller, int(r.n), int(r.s), round(r.pnb)] for r in cons.itertuples()]
segs = ["Jeunes actifs", "Familles", "Seniors", "Patrimonial", "Professionnels"]
cl = c.assign(parti=(c.statut_client != "Actif").astype(int), np=c.nb_produits.clip(upper=6)).groupby(
    ["id_agence", "segment", "np"]).agg(n=("parti", "size"), q=("parti", "sum"), t=("nb_produits", "sum")).reset_index()
cl_rows = [[ag[r.id_agence], segs.index(r.segment), int(r.np), int(r.n), int(r.q), int(r.t)] for r in cl.itertuples()]
data = {
    "agences": a.agence.tolist(), "regions": a.region.tolist(),
    "produits": p.produit.tolist(), "famProduit": [fam.index(f) for f in p.famille], "familles": fam,
    "canaux": canaux, "segments": segs,
    "cube": cube_rows, "obj": obj_rows, "cons": cons_rows, "clients": cl_rows,
}
js = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
tpl = (ROOT / "scripts" / "dashboard_template.html").read_text(encoding="utf-8")
(ROOT / "dashboard.html").write_text(tpl.replace("/*__DATA__*/null", js), encoding="utf-8")
print("dashboard.html", len(js) // 1024, "Ko de données")
