# Dashboard de performance commerciale bancaire

## Contexte

Ce projet personnel vise à construire un dashboard de performance commerciale bancaire à partir d'un dataset public de campagnes marketing.

L'objectif est d'analyser les profils clients, les canaux de contact, les campagnes commerciales et les indicateurs de conversion afin d'aider une agence bancaire à piloter son activité.

## Source des données

Les données principales proviennent du dataset public **Bank Marketing** de l'UCI Machine Learning Repository.

Source : https://archive.ics.uci.edu/dataset/222/bank+marketing

Le dataset contient 45 211 contacts de campagne. Certaines tables complémentaires ont été simulées afin de construire un cas métier complet de pilotage commercial bancaire.

## Problématique

Comment analyser la performance commerciale d'une campagne bancaire et identifier les profils clients les plus susceptibles de souscrire à un produit ?

## Objectifs du projet

- Suivre le taux de conversion des campagnes
- Analyser le portefeuille clients par profil
- Identifier les segments les plus performants
- Comparer les performances par canal de contact
- Suivre les indicateurs par agence et région
- Contrôler la qualité des données
- Construire un dashboard Power BI interactif

## Indicateurs clés

- Nombre total de contacts : 45 211
- Nombre de souscriptions : 5 289
- Taux de conversion global : 11,7 %
- Solde moyen client : 1 362,27
- Durée moyenne d'un contact : 4,3 minutes

  ## Aperçu du dashboard

## Aperçu du dashboard

### Vue d’ensemble

![Vue d’ensemble](images/Vue%20d'ensemble.png)

### Analyse du portefeuille clients

![Analyse du portefeuille clients](images/Analyse%20du%20portefeuille%20clients.png)

### Performance commerciale

![Performance commerciale](images/Performance%20commerciale.png)

### Qualité des données

![Qualité des données](images/Qualité%20des%20données.png)

## Tables préparées

- `contacts_campagne_bancaire.csv`
- `agences.csv`
- `produits.csv`
- `qualite_donnees.csv`
- `resume_kpi.csv`

## Pages prévues du dashboard

### 1. Vue d'ensemble

- Contacts
- Souscriptions
- Taux de conversion
- Solde moyen
- Conversion par mois

### 2. Analyse clients

- Répartition par âge
- Répartition par profession
- Répartition par statut marital
- Solde moyen par segment
- Souscription selon les crédits existants

### 3. Performance commerciale

- Conversion par canal de contact
- Conversion par intensité de campagne
- Performance par agence
- Performance par région

### 4. Qualité des données

- Taux de valeurs inconnues
- Champs à fiabiliser
- Impact potentiel sur l'analyse

## Compétences travaillées

- Analyse exploratoire
- Nettoyage et préparation de données
- Modélisation de données
- Création de KPI
- Segmentation client
- Power BI
- SQL / Python
- Reporting commercial
- Data quality


