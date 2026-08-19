---
name: wcvp-name-resolution
description: Résoudre un nom de plante contre la nomenclature de référence WCVP (Kew) et l'étendre à tous ses synonymes avant toute recherche de données. À utiliser dès qu'un nom d'espèce végétale sert de clé de jointure — recherche de composés, d'occurrences, de spectres ou de littérature. Indispensable avant d'affirmer qu'une plante « n'a pas de données ».
---

# Résolution de noms de plantes (WCVP)

## Pourquoi cette étape n'est jamais optionnelle

Une plante change de nom. Les genres sont redécoupés, les espèces sont fusionnées, les
hybrides sont notés de trois façons différentes. Si vous cherchez des données sous un
seul nom, vous obtiendrez une absence — et vous la prendrez pour un fait.

Cas réels, tous rencontrés en production :

| Nom cherché | Nom sous lequel la chimie existe | Composés manqués |
| --- | --- | --- |
| *Vetiveria zizanioides* | *Chrysopogon zizanioides* | 44 |
| *Wedelia trilobata* | *Sphagneticola trilobata* | 78 |
| *Chamaesyce hirta* | *Euphorbia hirta* | 86 |
| *Ocimum sanctum* | *Ocimum tenuiflorum* | 106 |
| *Eucalyptus citriodora* | *Corymbia citriodora* | 108 |
| *Citrus aurantium* | *Citrus deliciosa* | 573 |
| *Hibiscus rosa-sinensis* | *Hibiscus × rosa-sinensis* | 25 |
| *Paeonia suffruticosa* | *Paeonia × suffruticosa* | — |

Dans une analyse réelle, **10 noms sur 33** issus d'une liste botanique de référence
publiée en 2006 étaient devenus des synonymes. Sans expansion, 30 % du jeu de données
aurait été déclaré « sans chimie décrite » à tort.

## Procédure

1. **Obtenir WCVP.** Archive publique de Kew, ~84 Mo :
   `https://sftp.kew.org/pub/data-repositories/WCVP/wcvp.zip`
   Contient `wcvp_names.csv` (1,45 M noms) et `wcvp_distribution.csv`, séparateur `|`.

2. **Résoudre.** Pour chaque nom, trouver `accepted_plant_name_id`.

3. **Étendre.** Récupérer TOUS les `taxon_name` pointant vers ce même identifiant
   accepté. C'est l'ensemble de recherche.

4. **Normaliser.** Avant toute comparaison de chaînes, appliquer la normalisation des
   hybrides et des rangs infraspécifiques (voir `scripts/resolve.py`).

5. **Chercher sur l'union**, jamais sur le nom d'entrée seul.

## Normalisation obligatoire

Trois pièges distincts, à traiter systématiquement :

- **Hybrides** : `Citrus × limon`, `Citrus x limon`, `Citrus limon` doivent s'apparier.
  Le signe `×` (U+00D7) et la lettre `x` ne sont pas le même caractère.
- **Rangs infraspécifiques** : `Raphanus raphanistrum subsp. sativus` doit pouvoir
  s'apparier à `Raphanus raphanistrum`.
- **Espaces multiples et casse**.

## Utilisation

```bash
python scripts/resolve.py --names "Vetiveria zizanioides" "Wedelia trilobata" \
                          --wcvp /chemin/vers/wcvp_names.csv
```

Sortie JSON : nom d'entrée, nom accepté, identifiant WCVP, liste complète des noms de
recherche, et famille.

## Contrôle de qualité à rapporter

Toujours publier, avec tout résultat fondé sur des noms :

- le taux de résolution (combien de noms appariés sur le total) ;
- le nombre de noms d'entrée qui sont des synonymes ;
- le nombre total de noms de recherche générés ;
- la liste des noms non résolus.

Un résultat qui ne rapporte pas son taux d'appariement n'est pas vérifiable.

## Rangs et pièges résiduels

- WCVP couvre les **plantes vasculaires**. Les algues, mousses et champignons en sont
  absents : une absence dans WCVP ne veut rien dire pour eux.
- Certains noms sont marqués `Unplaced` ou `Artificial Hybrid` — les traiter à part.
- La correspondance avec la taxonomie NCBI (utilisée par les dépôts de spectres) et
  avec le backbone GBIF n'est pas exacte. Prévoir une étape de réconciliation
  supplémentaire quand vous croisez ces sources.
