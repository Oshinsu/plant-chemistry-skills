---
name: lotus-chemistry-lookup
description: Chercher quels produits naturels sont décrits pour un taxon donné, via LOTUS hébergé dans Wikidata (propriété P703). À utiliser pour savoir si la chimie d'une espèce a déjà été publiée, ou pour mesurer la couverture chimique d'un groupe de plantes. Inclut un garde-fou obligatoire contre les requêtes silencieusement cassées.
---

# Chimie décrite d'un taxon (LOTUS via Wikidata)

## Ce que LOTUS est, et n'est pas

LOTUS (Rutz *et al.* 2022, *eLife*, CC0) relie des structures chimiques aux organismes
qui les produisent. Il est hébergé dans Wikidata : un composé pointe vers son organisme
par la propriété **P703** (« présent dans le taxon »).

**LOTUS est une borne inférieure de la littérature, pas la littérature.** Une molécule
publiée dans un article non indexé n'y figure pas. *Atropa belladonna* — la belladone,
source de l'atropine, dans tous les manuels — peut apparaître sans composé.

La formulation défendable est donc toujours :

> *absente des corpus chimiques machine-lisibles*

et jamais :

> ~~jamais étudiée~~

C'est une distinction de fond : ce qui n'est pas dans ces bases est invisible pour tout
modèle entraîné dessus, quelle que soit la littérature papier existante.

## Le piège qui a produit un faux résultat publié

`P703` relie les composés aux items **espèce**. Compter `P703` directement sur un item
**genre** renvoie presque toujours zéro.

Une analyse réelle a ainsi conclu que les genres *Buxus*, *Vanilla*, *Eugenia* et
*Miconia* n'avaient **aucune chimie décrite** — alors que les alcaloïdes de *Buxus* et
la vanilline sont des classiques. Il fallait traverser `P171` (taxon parent) vers les
espèces filles.

```sparql
# FAUX : renvoie 0 pour presque tout genre
SELECT (COUNT(DISTINCT ?c) AS ?n) WHERE {
  ?g wdt:P225 "Buxus" . OPTIONAL { ?c wdt:P703 ?g . }
}

# CORRECT : passe par les espèces filles
SELECT (COUNT(DISTINCT ?c) AS ?n) WHERE {
  ?g wdt:P225 "Buxus" ; wdt:P105 wd:Q34740 .
  ?sp wdt:P171 ?g .
  OPTIONAL { ?c wdt:P703 ?sp . }
}
```

## Garde-fou obligatoire

**Aucun chiffre ne doit sortir d'une requête qui n'a pas passé le test des témoins.**

Le script refuse de s'exécuter s'il ne retrouve pas la chimie d'espèces massivement
publiées :

| Témoin | Plancher attendu |
| --- | ---: |
| *Catharanthus roseus* | 100 composés |
| *Coffea arabica* | 50 |
| *Buxus sempervirens* | 30 |
| *Vanilla planifolia* | 20 |

Ce garde-fou a réellement intercepté le bug `P703`-sur-genre décrit ci-dessus, avant
publication.

## Avant d'interroger : résoudre les noms

Toujours passer par `wcvp-name-resolution` et chercher sur l'union
{nom d'entrée} ∪ {nom accepté} ∪ {tous les synonymes}. Une recherche sur le seul nom
d'entrée produit des absences fausses — et elles vont systématiquement dans le sens
qui vous arrange.

## Utilisation

```bash
python scripts/lookup.py --names "Inga martinicensis" "Hyptis atrorubens"
python scripts/lookup.py --file search_names.txt --level genus --out chimie.json
```

## Sources complémentaires

LOTUS seul sous-estime. Pour une porte A plus large, croiser avec :

- **Kew VascularPlantChemodiversity** — `doi:10.5281/zenodo.19224646`, CC BY 4.0,
  407 676 couples composé-organisme sur 26 105 espèces, Wikidata **et** KNApSAcK,
  noms déjà résolus contre WCVP, annotations NPClassifier incluses. C'est la source la
  plus complète et la moins coûteuse à réutiliser.
- **COCONUT** — CC0, dump téléchargeable.
- **NPAtlas** — attention, **CC BY-NC** depuis la version 2024_09 : ne pas mélanger à
  un jeu de données qui se veut ouvert.
