# Etape 1 - Compréhension des données

## Source des données

Le projet utilise le dataset public **Bank Marketing** de l'UCI Machine Learning Repository.

Ce jeu de données contient les résultats de campagnes marketing directes menées par une banque portugaise. L'objectif de la campagne était de proposer un produit bancaire de type **dépôt à terme**.

Source : https://archive.ics.uci.edu/dataset/222/bank+marketing

## Volume

- Nombre de lignes : 45 211 contacts de campagne
- Nombre de souscriptions : 5 289
- Taux de conversion global : 11,7 %
- Solde moyen client : 1 362,27
- Durée moyenne d'un contact : 4,3 minutes

## Objectif métier

L'objectif du projet est de construire un dashboard de performance commerciale bancaire permettant de répondre à ces questions :

- Quel est le taux de conversion des campagnes ?
- Quels profils clients souscrivent le plus au produit bancaire ?
- Quels canaux de contact sont les plus performants ?
- Quels segments clients ont les meilleurs soldes moyens ?
- Quelles agences ou régions performent le mieux ?
- Quels problèmes de qualité de données peuvent impacter l'analyse ?

## Tables préparées pour Power BI

### contacts_campagne_bancaire.csv

Table principale du projet. Elle contient les informations clients, les caractéristiques de campagne et la cible de conversion.

Colonnes principales :

- `contact_id` : identifiant unique du contact
- `client_id` : identifiant client simulé
- `agency_id` : identifiant agence simulé
- `age` : âge du client
- `age_segment` : tranche d'âge
- `job_fr` : catégorie professionnelle
- `marital_fr` : statut marital
- `education_fr` : niveau d'éducation
- `balance` : solde moyen annuel
- `balance_segment` : tranche de solde
- `has_default` : indicateur de défaut de paiement
- `has_housing_loan` : indicateur de crédit immobilier
- `has_personal_loan` : indicateur de crédit personnel
- `contact_fr` : canal de contact
- `month_name` : mois de contact
- `duration` : durée du contact en secondes
- `contact_duration_min` : durée du contact en minutes
- `campaign` : nombre de contacts pendant la campagne
- `campaign_intensity` : segment d'intensité de contact
- `previous_outcome_fr` : résultat de la campagne précédente
- `subscribed` : indicateur de souscription au produit

### agences.csv

Table simulée pour enrichir l'analyse commerciale par réseau.

Colonnes :

- `agency_id` : identifiant agence
- `agency_name` : nom de l'agence
- `region` : région
- `city` : ville

### produits.csv

Table de référence produit.

Colonnes :

- `product_id` : identifiant produit
- `product_name` : nom du produit
- `product_family` : famille produit
- `description` : description métier

### qualite_donnees.csv

Table de suivi de la qualité des données.

Colonnes :

- `field_name` : champ analysé
- `unknown_count` : nombre de valeurs inconnues
- `row_count` : nombre total de lignes
- `unknown_rate` : taux de valeurs inconnues

## Remarque importante

Certaines tables complémentaires, comme les agences et les produits, sont simulées pour construire un cas métier plus complet. Les données principales de campagne restent issues d'une source publique.
