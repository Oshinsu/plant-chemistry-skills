---
name: gbif-collection-effort
description: Mesurer l'effort de collecte d'une espèce ou d'un territoire via GBIF, et l'utiliser comme covariable de contrôle. À utiliser dans toute analyse où « cette espèce a-t-elle été étudiée » est la variable expliquée — l'effort de collecte est presque toujours le facteur dominant, et l'omettre invalide le résultat.
---

# Effort de collecte (GBIF)

## Pourquoi c'est la variable la plus importante

Dans toute analyse de couverture — chimique, génomique, fonctionnelle — la probabilité
qu'une espèce ait été étudiée dépend d'abord du nombre de fois où des humains l'ont
rencontrée. Si vous ne contrôlez pas cet effort, vous mesurez l'histoire des herbiers
et vous croyez mesurer la biologie.

Corrélation mesurée sur 3 042 espèces : **0,495** entre effort de collecte et présence
d'une chimie décrite, contre **0,220** pour l'aire native. L'effort domine.

## Comment le mesurer

**Effort mondial d'une espèce** : nombre total d'occurrences GBIF, tous pays confondus.

```
GET https://api.gbif.org/v1/species/match?name={nom}&kingdom=Plantae   -> usageKey
GET https://api.gbif.org/v1/occurrence/search?speciesKey={key}&limit=0 -> count
```

**Inventaire d'un territoire** : facette sur `speciesKey`.

```
GET https://api.gbif.org/v1/occurrence/search
      ?country=MQ&taxonKey=7707728&limit=0&facet=speciesKey&facetLimit=5000
```

`taxonKey=7707728` = Tracheophyta (plantes vasculaires).

Pour de gros volumes, préférer les téléchargements SQL de GBIF (compte gratuit requis,
un DOI est généré et doit être cité).

## Trois pièges à connaître

**Le nombre de pays n'est pas une aire de répartition.** Il additionne aire native,
naturalisation, horticulture et erreurs de géoréférencement, et subit le découpage
politique — un endémique du Brésil marque 1 comme un endémique d'une petite île.
Corrélation avec l'effort : **0,846**. Pour l'aire, utilisez WCVP.

**`establishmentMeans` est inexploitable.** Sur un jeu de 48 526 occurrences réel, il
n'était renseigné que sur **27** d'entre elles. Ne comptez pas dessus pour distinguer
autochtone et introduit.

**Les clés dupliquées faussent les listes.** 47 noms sur 3 780 portaient 2 à 3
`speciesKey` distincts, dont 33 avec des étendues discordantes — la même espèce comptée
dans deux classes d'aire. La clé secondaire est systématiquement la plus étroite, donc
elle contamine les listes « espèces rares ». Dédoublonnez par nom accepté en gardant la
clé au plus grand nombre d'occurrences.

## Le paradoxe territorial

Mieux un territoire est prospecté, **plus basse** paraît sa couverture chimique — parce
qu'on y a découvert davantage d'espèces obscures. Corrélation mesurée entre effort d'un
territoire et sa couverture : **−0,852**.

Ne comparez donc jamais des territoires sur leur pourcentage de couverture brute.

## Utilisation

```bash
python scripts/effort.py --names "Inga martinicensis" "Hyptis atrorubens"
python scripts/effort.py --country MQ --checklist          # inventaire territorial
python scripts/effort.py --file noms.txt --out effort.json
```

## Stratifier plutôt que modéliser

Pour contrôler l'effort, la stratification en quintiles est préférable à une covariable
dans un modèle : elle est non paramétrique, immunisée à la colinéarité, et se lit
directement. Si votre effet disparaît à l'intérieur des strates, il n'existait pas.
