# Automatisation du SAV Free Mobile : analyse des tweets clients avec NLP, LLM, RAG, Streamlit et Power BI

## Contexte

Projet de fin d’études (HETIC, Master Data & IA) sur un cas client Free Mobile.

Les clients utilisent Twitter pour signaler une panne, contester une facture ou demander de l’aide. Ces messages arrivent en grand nombre, sans structure, et doivent être lus un par un par les équipes SAV. L’objectif du projet était d’automatiser toute la chaîne : nettoyer les tweets, les classer avec un LLM, proposer une réponse, puis donner aux équipes des outils pour piloter et traiter les demandes.

## Problématique

Comment transformer des milliers de tweets clients non structurés en demandes classées, priorisées et routées vers la bonne équipe, avec une réponse déjà proposée ?

## Résultats clés

- **6 310** tweets traités par le pipeline
- **2 989** tweets clients identifiés après filtrage et déduplication
- **33,7 %** de demandes détectées comme urgentes
- Sentiment moyen : **-0,78**
- Base de connaissances de **4 755** modèles de réponses utilisée pour le RAG
- **3 applications** livrées : pipeline de traitement, application SAV multi-profils, chatbot

## Architecture de la solution

```
Tweets bruts (CSV)
   │
   ├─ 1. Prétraitement Python ........ nettoyage, filtrage, déduplication
   ├─ 2. Enrichissement RAG .......... recherche sémantique dans la base de réponses
   ├─ 3. Classification LLM .......... thème, sentiment, urgence, gravité, résumé, réponse, équipe
   ├─ 4. Export CSV standardisé ...... 16 colonnes
   │
   ├─ Application SAV Streamlit ...... écrans Analyste, Manager, Agent SAV
   ├─ Chatbot RAG .................... questions clients en langage naturel
   └─ Dashboard Power BI ............. pilotage des indicateurs
```

<!-- CAPTURE (optionnel) : schéma d’architecture → images/architecture.png -->

---

## 1. Automatisation du prétraitement

Un script Python prépare automatiquement les tweets avant l’analyse :

- Correction de l’encodage et normalisation du texte (accents, emojis, liens, mentions)
- Suppression des réponses publiées par les comptes Free pour ne garder que les messages clients
- Détection de la langue
- Déduplication des tweets
- Premiers indicateurs par règles : mots-clés d’urgence, émotions, intentions

Résultat : sur 6 310 tweets, 2 989 messages clients exploitables.

## 2. Classification avec NLP et LLM

Chaque tweet client est envoyé à un LLM (**Mistral AI** via API, ou **Ollama** en local) avec un prompt structuré. Le modèle renvoie un JSON validé avec Pydantic :

| Champ | Contenu |
|---|---|
| Thème | Problème réseau, Facturation, Freebox, Portabilité, Ligne mobile, Résiliation, SAV, Livraison, Autre |
| Sentiment | positif, neutre, négatif |
| Urgence | score de 0 à 3 |
| Gravité | score de 0 à 3 |
| Résumé | une phrase de 20 mots maximum |
| Réponse suggérée | réponse personnalisée prête à publier |
| Équipe de routage | SAV Mobile, Facturation, Technique, Freebox, Portabilité |
| Escalade | intervention humaine nécessaire ou non |

**Industrialisation du traitement :**

- Orchestration avec **LangChain**
- Traitement en parallèle (multithreading) avec limitation du nombre d’appels par minute
- **Cache SQLite** : un tweet déjà analysé n’est pas renvoyé au LLM, ce qui réduit le coût et le temps
- Normalisation des sorties (thèmes et sentiments harmonisés) et valeurs par défaut en cas d’erreur
- Export final en CSV standardisé de 16 colonnes, prêt pour l’application et Power BI

## 3. Enrichissement RAG

Avant la classification, chaque tweet est enrichi avec le contexte le plus proche dans une base de 4 755 modèles de réponses SAV :

- Encodage des textes avec un modèle **Sentence-Transformers** (DistilBERT multilingue)
- Recherche par similarité cosinus (Top-k)
- Injection du contexte trouvé dans le prompt du LLM
- Mise en cache des embeddings pour ne pas les recalculer

Le LLM s’appuie ainsi sur des réponses validées, ce qui rend ses suggestions plus pertinentes et plus cohérentes avec le ton de Free.

## 4. Application Streamlit : le pipeline en quelques clics

Une interface Streamlit permet de lancer tout le traitement sans écrire de code :

1. Import du fichier CSV de tweets
2. Lancement du prétraitement
3. Choix de la période et lancement de l’analyse LLM (Mistral ou Ollama)
4. Téléchargement du fichier enrichi

![Interface du pipeline Streamlit](images/streamlit-pipeline.png)

<!-- CAPTURE : étape « Traitement LLM » avec résultats → images/streamlit-traitement-llm.png -->

## 5. Application SAV Streamlit : 3 écrans métier

Une seconde application exploite les 2 989 tweets analysés, avec un écran par profil.

![Accueil de l’application SAV](images/streamlit-accueil.png)

**Analyste**
- Filtres par sentiment, thème, période et seuil de priorité
- Visualisations interactives (Altair) : thèmes, tendances, co-occurrences
- Export CSV et JSON

![Analyste : indicateurs et résultats détaillés](images/streamlit-analyste-resultats.png)

![Analyste : volumes par thème](images/streamlit-analyste-themes.png)

![Analyste : timeline et répartition horaire](images/streamlit-analyste-temps.png)

![Analyste : alertes automatiques](images/streamlit-analyste-alertes.png)

**Manager**
- KPI : volume de tweets, % urgents, % négatifs, auteurs uniques, urgence moyenne, tickets ouverts
- Onglets Vue globale, Alertes, Équipe
- Suivi de la charge par équipe

![Manager : indicateurs clés](images/streamlit-manager-kpi.png)

![Manager : volume quotidien, cumulé et auteurs les plus actifs](images/streamlit-manager-activite.png)

![Manager : sentiment et urgence vs sévérité](images/streamlit-manager-sentiment.png)

![Manager : statuts des tickets et heatmap jour × heure](images/streamlit-manager-operations.png)

![Manager : volumes et urgence par équipe](images/streamlit-manager-equipes.png)

![Manager : répartition des urgences et thèmes en progression](images/streamlit-manager-insights.png)

**Agent SAV**
- File d’attente triée par un **score de priorité** (urgence 45 %, gravité 40 %, sentiment négatif 15 %)
- Réponse suggérée par le LLM, modifiable avant envoi
- Actions rapides : répondre, réaffecter, clore
- Historique des modifications sauvegardé

![Agent SAV : indicateurs](images/streamlit-agent-kpi.png)

![Agent SAV : file d’attente priorisée et actions rapides](images/streamlit-agent-file.png)

## 6. Chatbot RAG

Un assistant conversationnel répond aux questions des clients Free Mobile :

- Base vectorielle **ChromaDB** construite à partir de questions-réponses Free Mobile
- Embeddings **Ollama** (mxbai-embed-large)
- Génération avec **Llama 3.3 70B** via Groq, ou un modèle local Ollama
- Interface de chat Streamlit

<!-- CAPTURE : conversation avec le chatbot → images/chatbot.png -->

## 7. Dashboard Power BI

Les résultats du pipeline alimentent un dashboard Power BI de pilotage du SAV.

### Vue d’ensemble

![Vue d’ensemble](images/dashboard-vue-ensemble.png)

### Analyse temporelle et opérationnelle

![Analyse temporelle](images/dashboard-analyse-temporelle.png)

### Urgence et performance

![Urgence et performance](images/dashboard-urgence-performance-floute.png)

### Analyse de sentiment

![Analyse de sentiment](images/dashboard-analyse-sentiment.png)

### Doublons, urgence et performance

![Doublons, urgence et performance](images/dashboard-doublon-urgence-performance.png)

---

## Stack technique

- **Python** : Pandas, NumPy, Pydantic
- **NLP / LLM** : Mistral AI, Ollama, LangChain, Llama 3.3 (Groq)
- **RAG** : Sentence-Transformers (DistilBERT multilingue), ChromaDB, PyTorch
- **Applications** : Streamlit, Altair, Plotly
- **Données** : SQLite (cache), CSV
- **BI** : Power BI, DAX, Power Query
- **Outils** : Git, GitHub

## Impact

- Les tweets clients ne sont plus lus un par un : ils arrivent classés, résumés et priorisés.
- Les demandes urgentes remontent en tête de la file d’attente des agents.
- Chaque demande est routée vers la bonne équipe, avec une réponse déjà proposée.
- Les managers suivent en continu les volumes, les urgences et le sentiment client.

## Pistes d’amélioration

- Connecter le pipeline à une source de tweets en temps réel
- Mesurer la qualité des classifications sur un échantillon annoté
- Déployer l’application SAV et le chatbot en ligne
- Suivre l’évolution du sentiment avant et après réponse
