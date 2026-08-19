---
name: natural-product-databases
description: Choisir la bonne base de produits naturels et connaître sa licence avant de l'utiliser. À consulter avant tout téléchargement ou redistribution de données de produits naturels — plusieurs bases majeures sont non commerciales ou sans licence, et les mélanger contamine juridiquement le jeu de données résultant.
---

# Bases de produits naturels : quoi utiliser, et sous quelle licence

## Le piège juridique

Les bases de produits naturels n'ont pas les mêmes conditions, et l'une d'elles a
changé de licence en cours de route. Mélanger du CC0 et du CC BY-NC dans un jeu
redistribué rend l'ensemble inexploitable commercialement — et souvent impossible à
démêler des années plus tard.

| Base | Licence | Réutilisable | Contenu |
| --- | --- | --- | --- |
| **LOTUS** | **CC0** | oui, sans condition | structures ↔ organismes, via Wikidata P703 |
| **COCONUT** | **CC0** | oui, sans condition | agrégat de produits naturels, dump téléchargeable |
| **Kew VascularPlantChemodiversity** | **CC BY 4.0** | oui, avec attribution | 407 676 couples composé-organisme, 26 105 espèces, noms résolus WCVP, annotations NPClassifier |
| **WCUPS** (usages) | **CC BY 4.0** | oui, avec attribution | 40 292 espèces à usage humain, catégories standard |
| **NPAtlas** | **CC BY-NC** depuis 2024_09 | non commercial seulement | produits naturels microbiens |
| **ANPDB** | **CC BY-NC** | non commercial seulement | produits naturels africains |
| **LANaPDB** | **aucune licence déclarée** | juridiquement ambigu | Amérique latine, 8 pays |

**Règle** : pour un jeu de données qui se veut ouvert et reproductible, s'en tenir à
LOTUS, COCONUT et les sources Kew. Citer les trois indépendamment.

## Laquelle choisir

**Pour savoir si une espèce a une chimie décrite** : le jeu **Kew
VascularPlantChemodiversity** (`doi:10.5281/zenodo.19224646`) est le meilleur point de
départ. Il agrège Wikidata (donc LOTUS) **et** KNApSAcK, les noms sont déjà résolus
contre WCVP, et les annotations NPClassifier sont calculées. Il évite de reconstruire
la partie la plus longue du travail : la réconciliation nomenclaturale.

Interroger LOTUS directement reste utile comme **contrôle indépendant**.

**Pour les classes chimiques** : NPClassifier (code MIT, modèles et ontologie CC0,
API publique) reste l'état de l'art. ClassyFire est sous restriction non commerciale.

**Pour les usages humains** : WCUPS (Kew 2020, `doi:10.5063/F1CV4G34`). Publié en PDF
de 689 pages, extractible — le nom est sur une ligne, l'identifiant IPNI et les codes
d'usage sur la suivante, séparés par des barres verticales. Catégories : `AF` animal,
`EU` environnemental, `FU` combustible, `GS` ressources génétiques, `HF` alimentation
humaine, `IF` invertébrés, `MA` matériaux, `ME` médicinal, `PO` poisons, `SU` social.

## Aucune base n'est complète

Toutes sous-estiment, et pas au hasard. *Atropa belladonna* — source de l'atropine —
peut être absente d'une base majeure. Une espèce absente d'une base n'est pas une espèce
non étudiée.

Formulez toujours vos résultats comme **« absente de telle base à telle date »**, jamais
comme « jamais étudiée ». C'est la seule affirmation que vos données soutiennent — et
c'est déjà une affirmation forte, puisque ce qui n'est pas dans ces bases est invisible
pour tout modèle entraîné dessus.

## Citation

Ces trois sources doivent être citées séparément dès qu'elles sont réutilisées :

- Rutz A. *et al.* (2022). The LOTUS initiative for open knowledge management in natural
  products research. *eLife* 11:e70780.
- Richard-Bollans A. *et al.* VascularPlantChemodiversity, Zenodo,
  `doi:10.5281/zenodo.19224646`, CC BY 4.0.
- Diazgranados M. *et al.* (2020). World Checklist of Useful Plant Species. KNB,
  `doi:10.5063/F1CV4G34`, CC BY 4.0.
