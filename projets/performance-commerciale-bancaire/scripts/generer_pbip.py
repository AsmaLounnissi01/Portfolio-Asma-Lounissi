"""Génère le projet Power BI (format PBIP) du dashboard Banque Aurore :
modèle sémantique (tables CSV, relations, mesures DAX) et rapport de 4 pages.

Usage : python generer_pbip.py <dossier_sortie> <chemin_windows_des_csv>
"""
import json
import sys
import uuid
from pathlib import Path

OUT = Path(sys.argv[1])
CSV_DIR = sys.argv[2].rstrip("\\")
NAME = "Banque_Aurore"

# ======================================================================= MODELE
def csv_m(file, cols):
    types = ", ".join(f'{{"{c}", {t}}}' for c, t, _ in cols)
    keep = ", ".join(f'"{c}"' for c, _, _ in cols)
    return [
        "let",
        f'    Source = Csv.Document(File.Contents("{CSV_DIR}\\{file}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f"    Colonnes = Table.SelectColumns(Entetes, {{{keep}}}),",
        f'    Types = Table.TransformColumnTypes(Colonnes, {{{types}}}, "en-US")',
        "in",
        "    Types",
    ]

RENAME = {"pnb": "pnb_ligne", "montant": "montant_ligne", "agence": "Agence", "region": "Région", "conseiller": "Conseiller",
          "produit": "Produit", "famille": "Famille", "segment": "Segment", "canal": "Canal"}
T_TXT, T_INT, T_NUM, T_DATE = "type text", "Int64.Type", "type number", "type date"
DT = {T_TXT: "string", T_INT: "int64", T_NUM: "double", T_DATE: "dateTime"}

def table(name, file, cols, measures=(), hidden_cols=(), extra=None):
    t = {"name": name, "columns": [], "partitions": [{"name": name, "mode": "import",
         "source": {"type": "m", "expression": csv_m(file, cols)}}]}
    for c, typ, fmt in cols:
        col = {"name": RENAME.get(c, c), "dataType": DT[typ], "sourceColumn": c, "summarizeBy": "none"}
        if fmt:
            col["formatString"] = fmt
        if c in hidden_cols:
            col["isHidden"] = True
        t["columns"].append(col)
    if measures:
        t["measures"] = [{"name": n, "expression": e, "formatString": f} for n, e, f in measures]
    if extra:
        t.update(extra)
    return t

EUR, PCT, INT = "#,##0 €;-#,##0 €", "0.0 %;-0.0 %", "#,##0"
MEASURES = [
    ("PNB", "SUM(Opportunites[pnb_ligne])", EUR),
    ("PNB N-1", "CALCULATE([PNB], SAMEPERIODLASTYEAR(Calendrier[Date]))", EUR),
    ("Évolution PNB", "DIVIDE([PNB] - [PNB N-1], [PNB N-1])", "+0.0 %;-0.0 %"),
    ("Objectif PNB", "SUM(Objectifs[objectif_pnb])", EUR),
    ("Atteinte objectif", "DIVIDE([PNB], [Objectif PNB])", PCT),
    ("Opportunités traitées", "COUNTROWS(Opportunites)", INT),
    ("Ventes signées", 'CALCULATE(COUNTROWS(Opportunites), Opportunites[statut] = "Signé")', INT),
    ("Taux de transformation", "DIVIDE([Ventes signées], [Opportunités traitées])", PCT),
    ("Production crédit", 'CALCULATE(SUM(Opportunites[montant_ligne]), Opportunites[statut] = "Signé", Produits[Famille] = "Crédit")', EUR),
    ("Collecte épargne", 'CALCULATE(SUM(Opportunites[montant_ligne]), Opportunites[statut] = "Signé", Produits[Famille] = "Épargne")', EUR),
    ("Nombre de clients", "COUNTROWS(Clients)", INT),
    ("Clients partis", 'CALCULATE(COUNTROWS(Clients), Clients[statut_client] = "Parti en 2025")', INT),
    ("Attrition clients", "DIVIDE([Clients partis], [Nombre de clients])", PCT),
    ("Équipement moyen", "AVERAGE(Clients[nb_produits])", "0.0"),
    ("PNB moyen par conseiller", "DIVIDE([PNB], DISTINCTCOUNT(Opportunites[id_conseiller]))", EUR),
]

calendrier = {
    "name": "Calendrier", "dataCategory": "Time",
    "columns": [
        {"name": "Date", "dataType": "dateTime", "sourceColumn": "Date", "isKey": True, "formatString": "dd/mm/yyyy", "summarizeBy": "none"},
        {"name": "Annee", "dataType": "int64", "sourceColumn": "Annee", "summarizeBy": "none", "formatString": "0"},
        {"name": "MoisNum", "dataType": "int64", "sourceColumn": "MoisNum", "summarizeBy": "none", "isHidden": True},
        {"name": "Mois", "dataType": "string", "sourceColumn": "Mois", "sortByColumn": "MoisNum", "summarizeBy": "none"},
    ],
    "partitions": [{"name": "Calendrier", "mode": "import", "source": {"type": "m", "expression": [
        "let",
        "    Dates = List.Dates(#date(2024, 1, 1), 731, #duration(1, 0, 0, 0)),",
        '    T = Table.FromList(Dates, Splitter.SplitByNothing(), {"Date"}),',
        '    T1 = Table.TransformColumnTypes(T, {{"Date", type date}}),',
        '    A = Table.AddColumn(T1, "Annee", each Date.Year([Date]), Int64.Type),',
        '    M = Table.AddColumn(A, "MoisNum", each Date.Month([Date]), Int64.Type),',
        '    N = Table.AddColumn(M, "Mois", each {"janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."}{[MoisNum] - 1}, type text)',
        "in",
        "    N"]}}],
}

clients_cols = [("id_client", T_TXT, None), ("id_agence", T_TXT, None), ("segment", T_TXT, None), ("age", T_INT, None),
                ("tranche_age", T_TXT, None), ("anciennete_ans", T_NUM, None), ("nb_produits", T_INT, None),
                ("statut_client", T_TXT, None)]
clients = table("Clients", "clients.csv", clients_cols, hidden_cols=("id_client", "id_agence"))
# colonne texte pour l'axe « produits détenus »
clients["partitions"][0]["source"]["expression"][-3] = clients["partitions"][0]["source"]["expression"][-3] + ","
clients["partitions"][0]["source"]["expression"].insert(-2,
    '    Detenus = Table.AddColumn(Types, "Produits détenus", each if [nb_produits] >= 6 then "6 et +" else Text.From([nb_produits]), type text)')
clients["partitions"][0]["source"]["expression"][-1] = "    Detenus"
clients["columns"].append({"name": "Produits détenus", "dataType": "string", "sourceColumn": "Produits détenus", "summarizeBy": "none"})

model = {
    "name": NAME, "compatibilityLevel": 1567,
    "model": {
        "culture": "fr-FR", "sourceQueryCulture": "fr-FR", "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
        "tables": [
            table("Opportunites", "opportunites.csv",
                  [("id_opportunite", T_TXT, None), ("date", T_DATE, "dd/mm/yyyy"), ("id_agence", T_TXT, None),
                   ("id_conseiller", T_TXT, None), ("id_client", T_TXT, None), ("id_produit", T_TXT, None),
                   ("canal", T_TXT, None), ("statut", T_TXT, None), ("montant", T_NUM, EUR), ("pnb", T_NUM, EUR)],
                  MEASURES, hidden_cols=("id_opportunite", "id_agence", "id_conseiller", "id_client", "id_produit", "date")),
            table("Agences", "agences.csv", [("id_agence", T_TXT, None), ("agence", T_TXT, None), ("region", T_TXT, None)],
                  hidden_cols=("id_agence",)),
            table("Conseillers", "conseillers.csv", [("id_conseiller", T_TXT, None), ("conseiller", T_TXT, None),
                  ("id_agence", T_TXT, None), ("fonction", T_TXT, None), ("anciennete_ans", T_INT, None)],
                  hidden_cols=("id_conseiller", "id_agence")),
            table("Produits", "produits.csv", [("id_produit", T_TXT, None), ("produit", T_TXT, None), ("famille", T_TXT, None),
                  ("taux_pnb", T_NUM, "0.0 %")], hidden_cols=("id_produit",)),
            clients,
            table("Objectifs", "objectifs.csv", [("date", T_DATE, "dd/mm/yyyy"), ("id_agence", T_TXT, None), ("famille", T_TXT, None),
                  ("objectif_pnb", T_NUM, EUR)], hidden_cols=("date", "id_agence")),
            calendrier,
        ],
        "relationships": [
            {"name": str(uuid.uuid4()), "fromTable": f, "fromColumn": fc, "toTable": t, "toColumn": tc}
            for f, fc, t, tc in [
                ("Opportunites", "date", "Calendrier", "Date"), ("Opportunites", "id_agence", "Agences", "id_agence"),
                ("Opportunites", "id_conseiller", "Conseillers", "id_conseiller"), ("Opportunites", "id_produit", "Produits", "id_produit"),
                ("Objectifs", "date", "Calendrier", "Date"), ("Objectifs", "id_agence", "Agences", "id_agence"),
                ("Clients", "id_agence", "Agences", "id_agence")]],
        "annotations": [{"name": "PBI_QueryOrder", "value": json.dumps(
            ["Opportunites", "Agences", "Conseillers", "Produits", "Clients", "Objectifs", "Calendrier"])}],
    },
}

# ======================================================================= RAPPORT
def lit(v):
    return {"expr": {"Literal": {"Value": v}}}

def s(t):  # chaîne littérale Power BI
    return lit("'" + t.replace("'", "''") + "'")

def color(c):
    return {"solid": {"color": lit("'" + c + "'")}}

ALIAS = {"Opportunites": "o", "Agences": "a", "Conseillers": "c", "Produits": "p", "Clients": "cl", "Objectifs": "ob", "Calendrier": "d"}

class Q:
    def __init__(self):
        self.ents, self.sel, self.order = [], [], []
    def _src(self, e):
        if e not in self.ents:
            self.ents.append(e)
        return {"SourceRef": {"Source": ALIAS[e]}}
    def col(self, e, p):
        p = RENAME.get(p, p)
        ref = f"{e}.{p}"
        self.sel.append({"Column": {"Expression": self._src(e), "Property": p}, "Name": ref, "NativeReferenceName": p})
        return ref
    def m(self, p, e="Opportunites"):
        ref = f"{e}.{p}"
        self.sel.append({"Measure": {"Expression": self._src(e), "Property": p}, "Name": ref, "NativeReferenceName": p})
        return ref
    def sort(self, kind, e, p, direction):
        p = RENAME.get(p, p) if kind == "c" else p
        key = "Measure" if kind == "m" else "Column"
        self.order.append({"Direction": direction, "Expression": {key: {"Expression": self._src(e), "Property": p}}})
    def build(self):
        q = {"Version": 2, "From": [{"Name": ALIAS[e], "Entity": e, "Type": 0} for e in self.ents], "Select": self.sel}
        if self.order:
            q["OrderBy"] = self.order
        return q

z = [0]
def container(x, y, w, h, single, filters=None):
    z[0] += 1000
    name = uuid.uuid4().hex[:20]
    cfg = {"name": name, "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z[0], "width": w, "height": h, "tabOrder": z[0]}}],
           "singleVisual": single}
    return {"x": x, "y": y, "z": z[0], "width": w, "height": h, "config": json.dumps(cfg, ensure_ascii=False),
            "filters": json.dumps(filters or [], ensure_ascii=False)}

def title_vc(text, extra=None):
    vc = {"title": [{"properties": {"show": lit("true"), "text": s(text), "fontSize": lit("12D"),
                                   "fontColor": color("#0B2545"), "bold": lit("true")}}]}
    if extra:
        vc.update(extra)
    return vc

def header(text, sub):
    shape = {"visualType": "shape", "drillFilterOtherVisuals": True, "objects": {
        "shape": [{"properties": {"tileShape": s("rectangle")}}],
        "fill": [{"properties": {"fillColor": color("#0B2545")}, "selector": {"id": "default"}}],
        "outline": [{"properties": {"show": lit("false")}}],
        "text": [{"properties": {"show": lit("true")}},
                 {"properties": {"text": s(text), "fontColor": color("#FFFFFF"), "fontSize": lit("20D"), "bold": lit("true"),
                                 "horizontalAlignment": s("left"), "leftMargin": lit("24D")}, "selector": {"id": "default"}}]},
        "vcObjects": {"background": [{"properties": {"show": lit("false")}}], "dropShadow": [{"properties": {"show": lit("false")}}],
                      "border": [{"properties": {"show": lit("false")}}]}}
    subtitle = {"visualType": "textbox", "drillFilterOtherVisuals": True, "objects": {"general": [{"properties": {"paragraphs": [
        {"textRuns": [{"value": sub, "textStyle": {"fontSize": "10pt", "color": "#CFE8F5"}}], "horizontalTextAlignment": "right"}]}}]},
        "vcObjects": {"background": [{"properties": {"show": lit("false")}}], "dropShadow": [{"properties": {"show": lit("false")}}],
                      "border": [{"properties": {"show": lit("false")}}]}}
    return [container(0, 0, 1280, 64, shape), container(760, 18, 500, 32, subtitle)]

def slicer(x, y, w, ent, prop, label, preset=None):
    q = Q(); ref = q.col(ent, prop)
    objs = {"data": [{"properties": {"mode": s("Dropdown")}}],
            "header": [{"properties": {"show": lit("true"), "text": s(label)}}]}
    if preset is not None:
        objs["general"] = [{"properties": {"filter": {"filter": {"Version": 2, "From": [{"Name": "d", "Entity": ent, "Type": 0}],
            "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": prop}}],
                                             "Values": [[{"Literal": {"Value": preset}}]]}}}]}}}}]
    sv = {"visualType": "slicer", "projections": {"Values": [{"queryRef": ref, "active": True}]}, "prototypeQuery": q.build(),
          "drillFilterOtherVisuals": True, "objects": objs}
    return container(x, y, w, 58, sv)

def slicers(famille=True, annee=True):
    out = []
    x = 24
    if annee:
        out.append(slicer(x, 74, 150, "Calendrier", "Annee", "Année", "2025L")); x += 162
    out.append(slicer(x, 74, 220, "Agences", "region", "Région")); x += 232
    out.append(slicer(x, 74, 220, "Agences", "agence", "Agence")); x += 232
    if famille:
        out.append(slicer(x, 74, 200, "Produits", "famille", "Famille de produits"))
    return out

def card(x, y, w, h, measure, label, accent):
    q = Q(); ref = q.m(measure)
    sv = {"visualType": "card", "projections": {"Values": [{"queryRef": ref}]}, "prototypeQuery": q.build(),
          "drillFilterOtherVisuals": True,
          "objects": {"labels": [{"properties": {"fontSize": lit("22D"), "color": color("#0B2545"), "labelDisplayUnits": lit("0D" if label == "PNB" else "1D"),
                                                 "labelPrecision": lit("0L") if label == "n" else lit("1L")}}],
                      "categoryLabels": [{"properties": {"show": lit("true"), "fontSize": lit("10D")}}]},
          "vcObjects": {"title": [{"properties": {"show": lit("false")}}],
                        "border": [{"properties": {"show": lit("true"), "color": color("#E6EAF0"), "radius": lit("12D")}}],
                        "padding": [{"properties": {"top": lit("4D"), "bottom": lit("4D"), "left": lit("4D"), "right": lit("4D")}}]}}
    # liseré coloré à gauche
    bar = {"visualType": "shape", "drillFilterOtherVisuals": True, "objects": {
        "shape": [{"properties": {"tileShape": s("rectangleRounded")}}],
        "fill": [{"properties": {"fillColor": color(accent)}, "selector": {"id": "default"}}],
        "outline": [{"properties": {"show": lit("false")}}]},
        "vcObjects": {"background": [{"properties": {"show": lit("false")}}], "dropShadow": [{"properties": {"show": lit("false")}}],
                      "border": [{"properties": {"show": lit("false")}}]}}
    return [container(x, y, w, h, sv), container(x + 2, y + 18, 5, h - 36, bar)]

def chart(x, y, w, h, vtype, title, cat, values, colors=None, y2=None, sort=None, labels=True, filters=None, extra_obj=None):
    q = Q()
    proj = {}
    if cat:
        proj["Category"] = [{"queryRef": q.col(*cat), "active": True}]
    proj["Y"] = [{"queryRef": q.m(v)} for v in values]
    if y2:
        proj["Y2"] = [{"queryRef": q.m(v)} for v in y2]
    if sort:
        q.sort(*sort)
    objs = {"labels": [{"properties": {"show": lit("true" if labels else "false"), "fontSize": lit("9D"), "color": color("#1B2430")}}],
            "categoryAxis": [{"properties": {"showAxisTitle": lit("false"), "fontSize": lit("9D")}}],
            "valueAxis": [{"properties": {"showAxisTitle": lit("false"), "fontSize": lit("9D"), "gridlineColor": color("#E6EAF0")}}],
            "legend": [{"properties": {"show": lit("true" if (len(values) + len(y2 or [])) > 1 else "false"),
                                       "position": s("Top"), "fontSize": lit("9D")}}]}
    dp = [{"properties": {"defaultColor": color(colors[0])}}] if colors else []
    for i, v in enumerate(values + (y2 or [])):
        if colors and i < len(colors):
            dp.append({"properties": {"fill": color(colors[i])}, "selector": {"metadata": f"Opportunites.{v}"}})
    if dp:
        objs["dataPoint"] = dp
    if vtype == "lineClusteredColumnComboChart":
        objs["lineStyles"] = [{"properties": {"strokeWidth": lit("3D"), "lineStyle": s("solid")}},
                              {"properties": {"lineStyle": s("dashed")}, "selector": {"metadata": "Opportunites.Objectif PNB"}}]
    if extra_obj:
        objs.update(extra_obj)
    sv = {"visualType": vtype, "projections": proj, "prototypeQuery": q.build(), "drillFilterOtherVisuals": True,
          "objects": objs, "vcObjects": title_vc(title)}
    return container(x, y, w, h, sv, filters)

def donut(x, y, w, h, title, cat, measure, palette):
    q = Q(); c = q.col(*cat); m = q.m(measure); q.sort("m", "Opportunites", measure, 2)
    objs = {"labels": [{"properties": {"show": lit("true"), "labelStyle": s("Category, percent of total"), "fontSize": lit("10D")}}],
            "legend": [{"properties": {"show": lit("false")}}],
            "dataPoint": [{"properties": {"fill": color(col)}, "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0,
                "Left": {"Column": {"Expression": {"SourceRef": {"Entity": cat[0]}}, "Property": RENAME.get(cat[1], cat[1])}},
                "Right": {"Literal": {"Value": "'" + val + "'"}}}}}]}} for val, col in palette.items()]}
    sv = {"visualType": "donutChart", "projections": {"Category": [{"queryRef": c, "active": True}], "Y": [{"queryRef": m}]},
          "prototypeQuery": q.build(), "drillFilterOtherVisuals": True, "objects": objs, "vcObjects": title_vc(title)}
    return container(x, y, w, h, sv)

def table_visual(x, y, w, h, title, cols, measures, sort_measure):
    q = Q(); refs = [q.col(*c) for c in cols] + [q.m(m) for m in measures]
    q.sort("m", "Opportunites", sort_measure, 2)
    objs = {"grid": [{"properties": {"rowPadding": lit("6D"), "textSize": lit("10D")}}],
            "columnHeaders": [{"properties": {"fontSize": lit("10D")}}],
            "values": [{"properties": {"fontSize": lit("10D")}}],
            "total": [{"properties": {"totals": lit("true")}}]}
    # mise en forme conditionnelle de l'atteinte (barres de données)
    objs["columnFormatting"] = [{"properties": {"dataBars": {"positiveColor": color("#13B5A6"), "negativeColor": color("#E4572E"),
                                 "axisColor": color("#0B2545"), "reverseDirection": lit("false"), "hideText": lit("false")}},
                                 "selector": {"metadata": "Opportunites.Atteinte objectif"}}]
    sv = {"visualType": "tableEx", "projections": {"Values": [{"queryRef": r} for r in refs]}, "prototypeQuery": q.build(),
          "drillFilterOtherVisuals": True, "objects": objs, "vcObjects": title_vc(title)}
    return container(x, y, w, h, sv)

def topn_filter(ent, prop, measure, n):
    prop = RENAME.get(prop, prop)
    return [{"name": uuid.uuid4().hex[:20], "expression": {"Column": {"Expression": {"SourceRef": {"Entity": ent}}, "Property": prop}},
             "filter": {"Version": 2, "From": [
                 {"Name": "subquery", "Expression": {"Subquery": {"Query": {"Version": 2,
                     "From": [{"Name": "c", "Entity": ent, "Type": 0}, {"Name": "o", "Entity": "Opportunites", "Type": 0}],
                     "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": prop}, "Name": "field"}],
                     "OrderBy": [{"Direction": 2, "Expression": {"Measure": {"Expression": {"SourceRef": {"Source": "o"}}, "Property": measure}}}],
                     "Top": n}}}, "Type": 2},
                 {"Name": "c", "Entity": ent, "Type": 0}],
                 "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": prop}}],
                                                 "Table": {"SourceRef": {"Source": "subquery"}}}}}]},
             "type": "TopN", "howCreated": 1, "isHiddenInViewMode": False}]

NAVY, SLATE, CYAN, TEAL, AMBER, RED, VIOLET, BLUE = "#0B2545", "#8DA9C4", "#00A3E0", "#13B5A6", "#F2A541", "#E4572E", "#8E6CCF", "#0B6FB8"
FAM = {"Crédit": BLUE, "Épargne": TEAL, "Assurance": AMBER, "Services": VIOLET}

def cards_row(items, y=144, h=96):
    n = len(items); gap = 12; w = (1232 - gap * (n - 1)) / n
    out = []
    for i, (m, lbl, acc) in enumerate(items):
        out += card(24 + i * (w + gap), y, w, h, m, lbl, acc)
    return out

pages = []
# ---- Page 1
v = header("Banque Aurore · Vue d’ensemble", "Données fictives · Pilotage commercial 2024-2025") + slicers()
v += cards_row([("PNB", "PNB", NAVY), ("Évolution PNB", "%", TEAL), ("Atteinte objectif", "%", TEAL),
                ("Taux de transformation", "%", CYAN), ("Production crédit", "PNB", BLUE), ("Collecte épargne", "PNB", TEAL)])
v.append(chart(24, 252, 800, 452, "lineClusteredColumnComboChart", "PNB mensuel, année précédente et objectif",
               ("Calendrier", "Mois"), ["PNB"], [NAVY, SLATE, AMBER], y2=["PNB N-1", "Objectif PNB"],
               sort=("c", "Calendrier", "Mois", 1), labels=False))
v.append(donut(836, 252, 420, 452, "Répartition du PNB par famille de produits", ("Produits", "famille"), "PNB", FAM))
pages.append(("Vue d’ensemble", v))
# ---- Page 2
v = header("Banque Aurore · Performance des agences", "PNB, objectifs et transformation par agence") + slicers()
v.append(chart(24, 144, 470, 560, "clusteredBarChart", "Atteinte de l’objectif PNB par agence", ("Agences", "agence"),
               ["Atteinte objectif"], [TEAL], sort=("m", "Opportunites", "Atteinte objectif", 2)))
v.append(table_visual(506, 144, 750, 340, "Tableau de bord des agences", [("Agences", "agence"), ("Agences", "region")],
                      ["PNB", "Objectif PNB", "Atteinte objectif", "Évolution PNB", "Taux de transformation"],
                      "Atteinte objectif"))
v.append(chart(506, 496, 750, 208, "clusteredColumnChart", "PNB par région : année et année précédente", ("Agences", "region"),
               ["PNB", "PNB N-1"], [NAVY, SLATE], sort=("m", "Opportunites", "PNB", 2)))
pages.append(("Agences", v))
# ---- Page 3
v = header("Banque Aurore · Produits, canaux et conseillers", "D’où vient le PNB et qui le génère") + slicers()
v.append(chart(24, 144, 610, 290, "clusteredBarChart", "PNB par produit", ("Produits", "produit"), ["PNB"], [BLUE],
               sort=("m", "Opportunites", "PNB", 2)))
v.append(chart(646, 144, 610, 290, "clusteredColumnChart", "Taux de transformation par canal", ("Opportunites", "canal"),
               ["Taux de transformation"], [CYAN], sort=("m", "Opportunites", "Taux de transformation", 2)))
v.append(chart(24, 446, 1232, 258, "clusteredColumnChart", "Top 10 des conseillers par PNB", ("Conseillers", "conseiller"),
               ["PNB"], [NAVY], sort=("m", "Opportunites", "PNB", 2), filters=topn_filter("Conseillers", "conseiller", "PNB", 10)))
pages.append(("Produits et conseillers", v))
# ---- Page 4
v = header("Banque Aurore · Clients : équipement et attrition", "Clients partis en 2025 selon leur équipement") + slicers(famille=False, annee=False)
v += cards_row([("Nombre de clients", "n", NAVY), ("Clients partis", "n", RED), ("Attrition clients", "%", RED), ("Équipement moyen", "Équipement", AMBER)])
v.append(chart(24, 252, 610, 452, "clusteredColumnChart", "Taux d’attrition selon le nombre de produits détenus",
               ("Clients", "Produits détenus"), ["Attrition clients"], [RED], sort=("c", "Clients", "Produits détenus", 1)))
v.append(chart(646, 252, 610, 452, "clusteredBarChart", "Taux d’attrition par segment de clientèle", ("Clients", "segment"),
               ["Attrition clients"], [AMBER], sort=("m", "Opportunites", "Attrition clients", 2)))
pages.append(("Clients", v))

sections = [{"name": "ReportSection" + uuid.uuid4().hex[:20], "displayName": n, "filters": "[]", "ordinal": i,
             "visualContainers": vcs, "config": "{}", "displayOption": 1, "width": 1280, "height": 720}
            for i, (n, vcs) in enumerate(pages)]
THEME = "Qualite_Donnees_-_Moderne7154435763540818.json"
report = {
    "config": json.dumps({"version": "5.43", "themeCollection": {
        "baseTheme": {"name": "CY24SU06", "version": "5.56", "type": 2},
        "customTheme": {"name": THEME, "version": {"visual": "2.1.0", "report": "3.0.0", "page": "2.3.0"}, "type": 1}},
        "activeSectionIndex": 0, "defaultDrillFilterOtherVisuals": True,
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": 1, "useNewFilterPaneExperience": True,
                     "allowChangeFilterTypes": True, "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True}}),
    "layoutOptimization": 0,
    "resourcePackages": [
        {"resourcePackage": {"name": "SharedResources", "type": 2, "items": [{"type": 202, "path": "BaseThemes/CY24SU06.json", "name": "CY24SU06"}], "disabled": False}},
        {"resourcePackage": {"name": "RegisteredResources", "type": 1, "items": [{"type": 201, "path": THEME, "name": THEME}], "disabled": False}}],
    "sections": sections,
}

# ======================================================================= ECRITURE
def w(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

PLAT = "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json"
w(OUT / f"{NAME}.pbip", {"version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}})
w(OUT / f"{NAME}.Report" / "definition.pbir", {"version": "1.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}, "byConnection": None}})
w(OUT / f"{NAME}.Report" / "report.json", report)
w(OUT / f"{NAME}.Report" / ".platform", {"$schema": PLAT, "metadata": {"type": "Report", "displayName": NAME}, "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}})
w(OUT / f"{NAME}.SemanticModel" / "definition.pbism", {"version": "1.0", "settings": {}})
w(OUT / f"{NAME}.SemanticModel" / "model.bim", model)
w(OUT / f"{NAME}.SemanticModel" / ".platform", {"$schema": PLAT, "metadata": {"type": "SemanticModel", "displayName": NAME}, "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}})
print("PBIP généré dans", OUT)
