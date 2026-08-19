# plant-chemistry-skills

**Skills Claude Code pour relier la biodiversité végétale à la chimie.**

Les outils pour *traiter* un spectre de masse ont déjà leurs skills — `matchms`,
`pyOpenMS`, RDKit, export GNPS/SIRIUS existent dans plusieurs paquets publics. Ce qui
manquait, c'est la couche qui répond à : **de quelle plante vient ce spectre, ce nom
est-il encore valide, et sa chimie est-elle déjà publiée quelque part ?**

Un scan de six paquets majeurs de skills scientifiques (`K-Dense-AI/scientific-agent-skills`,
`jaechang-hits/SciAgent-Skills`, `GPTomics/bioSkills`, `AlterLab-IEU/AlterLab-Academic-Skills`,
`dailycafi/metabolism-skills`, `BioTender-max/awesome-bio-agent-skills`) le confirme :
GBIF, WCVP, LOTUS, COCONUT, NPAtlas, résolution de noms, synonymes, occurrences,
herbiers, MassIVE et ethnobotanique en sont **tous absents**.

## Les six skills

| Skill | Répond à |
| --- | --- |
| `wcvp-name-resolution` | Ce nom est-il encore valide, et sous quels autres noms chercher ? |
| `lotus-chemistry-lookup` | Cette espèce a-t-elle une chimie décrite ? |
| `gbif-collection-effort` | Combien de fois cette plante a-t-elle été rencontrée ? |
| `redu-spectra-lookup` | Des spectres publics existent-ils déjà pour elle ? |
| `natural-product-databases` | Quelle base utiliser, sous quelle licence ? |
| `chemical-coverage-analysis` | Mon résultat de couverture tient-il debout ? |

## Pourquoi ce paquet existe

Il est né d'une analyse réelle de la flore des Petites Antilles qui a produit
**cinq conclusions successives, toutes fausses**, et les a rattrapées une par une :

1. « 91 % des endémiques n'ont aucune chimie décrite » — attendu sous H₀ : 0,29 taxon.
   Le test n'avait aucune puissance.
2. « 38 clades significativement sombres » — ligne de base gonflée par les cultures :
   tabac, tomate, mangue.
3. « 18 familles significatives, p en 10⁻⁶² » — non-indépendance phylogénétique,
   inflation ×1,87 par degré de liberté. Il en restait 5.
4. « L'étendue géographique détermine l'étude, OR ×34,8 » — le proxy d'aire était
   corrélé à 0,846 avec l'effort de collecte. L'effet s'inversait à effort constant.
5. « Le savoir traditionnel a guidé les paillasses, +24,5 points » — le filtre
   « cultivé » fait à la main manquait 56 espèces sur 98. Il restait +5,2.

Chacun de ces pièges est encodé dans un skill, avec les chiffres réels et le contrôle
qui l'attrape. C'est l'essentiel de ce que ce paquet apporte : pas des appels d'API,
des **garde-fous**.

## Le garde-fou le plus important

`lotus-chemistry-lookup` refuse de s'exécuter s'il ne retrouve pas la chimie d'espèces
massivement publiées — *Catharanthus roseus* ≥ 100 composés, *Coffea arabica* ≥ 50,
*Buxus sempervirens* ≥ 30, *Vanilla planifolia* ≥ 20.

Ce garde-fou a réellement intercepté un bug : la requête comptait la propriété `P703`
sur les items **genre** au lieu des items **espèce**, et concluait que *Buxus*,
*Vanilla*, *Eugenia* et *Miconia* n'avaient aucune chimie décrite. Les alcaloïdes de
*Buxus* et la vanilline auraient dit le contraire.

## Le piège des noms, en chiffres

Sur une liste botanique de référence de 33 espèces publiée en 2006, **10 noms étaient
devenus des synonymes**. Sans expansion, 30 % du jeu aurait été déclaré « sans chimie »
à tort.

| Nom cherché | Chimie réellement sous | Composés manqués |
| --- | --- | ---: |
| *Vetiveria zizanioides* | *Chrysopogon zizanioides* | 44 |
| *Wedelia trilobata* | *Sphagneticola trilobata* | 78 |
| *Chamaesyce hirta* | *Euphorbia hirta* | 86 |
| *Eucalyptus citriodora* | *Corymbia citriodora* | 108 |
| *Citrus aurantium* | *Citrus deliciosa* | 573 |

Les changements de genre, la notation hybride (`×` contre `x`) et les rangs
infraspécifiques cassent les jointures **silencieusement**, et toujours dans le sens
qui vous arrange : ils fabriquent des absences.

## Installation

```bash
git clone <ce-dépôt>
pip install requests numpy
```

Les skills sont lisibles tels quels. Chaque `SKILL.md` est autonome ; les scripts sont
utilisables en ligne de commande indépendamment de tout agent.

## Tests

Les tests ne vérifient pas que le code s'exécute — ils vérifient qu'il **attrape les
pièges** qui ont produit de faux résultats. Chaque cas de test est une erreur réellement
commise.

```bash
python tests/test_traps.py --wcvp /chemin/wcvp_names.csv            # hors ligne
python tests/test_traps.py --wcvp /chemin/wcvp_names.csv --online   # + Wikidata
```

Couvre : les six reclassements de genre qui font disparaître de la chimie, les quatre
formes de normalisation (signe multiplié contre lettre x, rangs infraspécifiques,
espaces), le garde-fou des témoins, et la traversée `P171` au niveau genre.

## Sources et licences

Les données restent sous la licence de leur source. Voir
`skills/natural-product-databases/SKILL.md` pour le tableau complet — **LOTUS et COCONUT
sont CC0, NPAtlas est passé en CC BY-NC, LANaPDB n'a aucune licence déclarée.**

À citer indépendamment en cas de réutilisation :

- Rutz A. *et al.* (2022). *eLife* 11:e70780 — LOTUS
- Govaerts R. *et al.* — World Checklist of Vascular Plants, RBG Kew
- Richard-Bollans A. *et al.* — VascularPlantChemodiversity, `doi:10.5281/zenodo.19224646`
- Diazgranados M. *et al.* (2020) — World Checklist of Useful Plant Species, `doi:10.5063/F1CV4G34`
- GBIF.org — occurrences et taxonomie
- Pan-ReDU — métadonnées des dépôts de spectrométrie de masse

## Licence

MIT pour le code et les skills. Voir `LICENSE`.
