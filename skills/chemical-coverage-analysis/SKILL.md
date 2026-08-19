---
name: chemical-coverage-analysis
description: Analyser correctement la couverture chimique d'un groupe de plantes — quelles espèces ont une chimie décrite et pourquoi. À utiliser AVANT toute affirmation du type « ces plantes sont inexplorées », « cette lignée est sous-étudiée » ou « cette région est un angle mort chimique ». Contient les six contrôles qui invalident la plupart de ces affirmations.
---

# Mesurer la couverture chimique sans se tromper

## L'avertissement principal

Presque toutes les analyses de couverture chimique mesurent **où les humains sont
passés**, et le prennent pour une propriété de la nature.

Ce skill existe parce que cinq conclusions successives d'une analyse réelle ont été
détruites par les contrôles décrits ici. À chaque fois, le mécanisme était le même :
l'effort de collecte confondait tout. Appliquez ces six contrôles avant de publier
quoi que ce soit.

---

## Contrôle 1 — Le taux de base

**Avant de dire « X % de ces espèces n'ont aucune chimie », mesurez ce que donne un
groupe témoin comparable.**

Cas réel : « 30 endémiques sur 33 sans aucun composé décrit, soit 91 % » — chiffre
spectaculaire. Puis le taux de base des genres concernés a été mesuré : **1,15 %** des
espèces tropicales de ces genres ont un composé décrit. Sous cette hypothèse nulle,
l'attendu était de **0,29 taxon** avec chimie. Observer zéro avait déjà **74 %** de
chance d'arriver.

Le résultat ne disait rien. Il mesurait la faiblesse de LOTUS sur les tropiques.

```python
# attendu sous H0, loi de Poisson-binomiale
ps = [base_rate[genus_of(sp)] for sp in taxa]
expected = sum(ps)
p_zero = prod(1 - p for p in ps)
```

---

## Contrôle 2 — La puissance du test

**Vérifiez que votre test PEUT rejeter avant de lire son résultat.**

Cas réel : un test annonçait « 0 clade significatif sur 38 » et le dépôt en tirait un
diagnostic de sous-puissance. La réalité était pire : avec un taux de base de 9,55 % et
une correction de Benjamini-Hochberg sur 38 clades, le p minimal atteignable par un
clade de *n* espèces vaut (1−p)ⁿ. **Un seul clade sur 38 pouvait mathématiquement
rejeter.** Le zéro était garanti par construction.

```python
# pour chaque clade, le p le plus petit possible
p_min = (1 - base_rate) ** n_species
can_reject = p_min <= 0.05 / n_tests
```

Si moins de la moitié de vos tests peuvent rejeter, votre « absence de signal » n'est
pas une mesure.

---

## Contrôle 3 — L'effort de collecte

**C'est le contrôle qui tue le plus de résultats. Ne le sautez jamais.**

La probabilité qu'une plante ait une chimie décrite dépend massivement du nombre de
fois où des humains l'ont rencontrée. Mesurez l'effort par le nombre total
d'occurrences mondiales GBIF, et refaites votre analyse à effort constant.

Cas réel, mesuré : la corrélation entre l'effort de collecte d'un territoire et sa
couverture chimique apparente était de **−0,852**. Les territoires les mieux prospectés
paraissent les moins bien couverts, parce que mieux on inventorie, plus on découvre
d'espèces obscures.

Méthode recommandée : **stratifier**, pas seulement modéliser. Découpez en quintiles
d'effort et comparez à l'intérieur de chaque strate. C'est non paramétrique, sans risque
de colinéarité, et immédiatement lisible.

---

## Contrôle 4 — Les proxys d'aire dérivés d'occurrences

**Un « nombre de pays GBIF » n'est pas une aire de répartition.**

Cas réel : une analyse concluait que l'étendue géographique déterminait massivement
qu'une plante soit étudiée, avec un odds ratio de **×34,8**. En remplaçant le proxy par
l'aire native curée de WCVP (établie à partir de flores, pas d'occurrences), l'effet
tombait à **×2,4** — puis **s'inversait** à effort constant.

Ce qui était mesuré n'était pas la biogéographie. C'était l'exposition.

Corrélations mesurées :

| Variable | avec l'effort de collecte |
| --- | ---: |
| nombre de pays GBIF | 0,846 |
| aire native WCVP (TDWG3) | 0,636 |

Utilisez toujours l'aire native WCVP, jamais un décompte d'occurrences.

**Limite de résolution à connaître** : TDWG niveau 3 ne descend pas sous la « région
botanique ». La Martinique, par exemple, est incluse dans `WIN` (Windward Is.) avec la
Dominique, Sainte-Lucie, Saint-Vincent et Grenade. Une aire de 1 unité ne veut pas dire
« endémique d'une île ».

---

## Contrôle 5 — La non-indépendance phylogénétique

**Les espèces d'un même genre ne sont pas des tirages indépendants.**

Cas réel : des p-values en 10⁻⁶² calculées avec `chi2.sf(stat, df)`. Un null construit
par permutation des étiquettes de famille **entre genres**, grappes de genre intactes,
donnait une moyenne de 86,7 là où la loi du khi-deux prédisait 46. Facteur d'inflation
**×1,87 par degré de liberté**.

Contrôle décisif : une permutation au niveau **espèce**, qui détruit la grappe, restitue
exactement la loi théorique (47,0 contre 46 attendus). L'inflation vient donc bien de la
structure phylogénétique.

Conséquence : après correction, une liste de **18 familles significatives est tombée
à 5**.

Ce qu'il faut faire :
- p-values par **permutation à grappes de genre**, jamais par loi asymptotique ;
- erreurs types **sandwich cluster-robustes** ;
- le genre est un **plancher** de correction, pas un plafond — grouper par famille
  augmente encore les erreurs types.

---

## Contrôle 6 — Les espèces cultivées

**Les plantes cultivées écrasent tout jeu de données de couverture chimique.**

Les espèces les mieux documentées d'une flore locale seront le tabac, la tomate, la
mangue, le gingembre — pas la flore spontanée. Un taux de couverture non filtré mesure
l'agronomie mondiale, pas la biodiversité locale.

Source propre pour filtrer : **World Checklist of Useful Plant Species** (Kew 2020,
CC BY 4.0, `doi:10.5063/F1CV4G34`), 40 292 espèces avec catégories d'usage standard —
`HF` alimentation humaine, `ME` médicinal, `MA` matériaux, etc. Elle permet de contrôler
l'usage **alimentaire** tout en gardant l'usage **médicinal** comme variable d'intérêt.

Cas réel : un contrôle fait à la main marquait 42 espèces comme cultivées. La liste Kew
en identifiait **98 sur 144**. Le résultat annoncé (+24,5 points) s'effondrait à +5,2 une
fois le vrai filtre appliqué.

---

## Le piège qui n'est pas un contrôle : le taux d'annotation

**Ne présentez jamais « la plupart des spectres ne correspondent à rien de connu »
comme une découverte.**

En métabolomique non ciblée, le taux d'annotation par recherche en bibliothèque est
notoirement de **2 à 10 %**. C'est le lieu commun fondateur de la discipline, cité en
introduction de chaque article, et la raison d'être de SIRIUS, DreaMS et consorts.

Retrouver ce chiffre n'est pas un résultat. C'est un contrôle de cohérence.

---

## Ce qui reste affirmable

Après ces contrôles, il reste des énoncés solides :

- des **décomptes descriptifs** sans modèle (« N espèces sur M n'ont aucun composé dans
  telle base, à telle date ») ;
- des **listes nommées** d'espèces vérifiables, qui sont des ressources utilisables ;
- des **effets de lignée** qui survivent à l'effort et à la permutation ;
- et le fait, robuste et souvent le plus intéressant, que **la couverture chimique est
  d'abord une carte de l'attention humaine**.
