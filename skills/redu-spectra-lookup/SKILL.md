---
name: redu-spectra-lookup
description: Trouver quelles espèces ont des spectres de masse déjà déposés publiquement, et localiser les fichiers correspondants. À utiliser pour savoir si des données expérimentales existent avant de planifier une collecte, ou pour croiser « chimie mesurée » et « chimie décrite ».
---

# Spectres publics par espèce (Pan-ReDU)

## La distinction qui fonde ce skill

Il existe deux façons différentes pour une plante d'être « connue chimiquement », et
elles ne sont pas corrélées comme on l'attend :

| | Porte A — **décrite** | Porte B — **mesurée** |
| --- | --- | --- |
| Quoi | un article dit « molécule X dans espèce Y », et quelqu'un l'a saisi en base | quelqu'un a passé un extrait au spectromètre et a déposé les données brutes |
| Sources | LOTUS, KNApSAcK, COCONUT | GNPS/MassIVE, MetaboLights, Metabolomics Workbench |
| Gardien | la publication et la curation bénévole | l'accès à un laboratoire et la culture de l'open data |

**Attention au sens exact de la porte B** : « un signal a été enregistré », **pas** « une
molécule a été identifiée ». Personne ne sait ce qu'il y a dans ces spectres.

Des espèces existent en porte B sans exister en porte A : leurs données dorment dans des
dépôts publics et aucune chimie n'a jamais été publiée pour elles. C'est une ressource
gratuite et inexploitée.

## Accès

**Dump ReDU** — métadonnées harmonisées de tous les dépôts, avec taxonomie NCBI :

```
GET https://redu.gnps2.org/dump
```

TSV volumineux (~844 Mo). Colonnes utiles : `ATTRIBUTE_DatasetAccession`, `filename`,
`NCBITaxonomy` (format `3816|Abrus precatorius`), `MassSpectrometer`,
`IonizationSourceAndPolarity`, `ChromatographyAndPhase`. À lire **en flux** en filtrant
sur vos espèces cibles.

**Cache de fichiers GNPS2** — chemins, tailles, comptages de spectres par fichier :

```
GET https://datasetcache.gnps2.org/datasette/database/filename.json
      ?dataset__exact=MSV000085119&_size=400
```

**Téléchargement d'un fichier MassIVE** :

```
GET https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile
      ?forceDownload=true&file=f.{dataset}/{chemin}
```

## Le seuil de robustesse

Une espèce vue dans **un seul jeu de données** est l'artefact d'un seul laboratoire.
Une espèce vue dans **deux jeux indépendants** est un fait. Sur un jeu réel de 3 325
espèces végétales, seules **994** passaient le seuil de deux jeux, et 538 celui de trois.

Retenez au minimum deux jeux, et dites-le dans la méthode.

## Pièges mesurés

**Les fichiers sont des plaques multi-espèces.** Savoir qu'une espèce est « dans le jeu »
ne suffit pas — un jeu peut contenir 394 fichiers couvrant toute une famille. Seul le
dump ReDU donne la correspondance fichier par fichier.

**Les formats sont mélangés.** mzML et mzXML coexistent dans le même dépôt et n'ont pas
le même lecteur ni le même chemin d'accès au précurseur.

**Les métadonnées de provenance sont quasi vides.** Sur un jeu réel, **95,7 %** des
lignes de plantes n'avaient aucun pays renseigné. Ne construisez aucune carte
géographique sur ReDU.

**L'effort est extrêmement concentré.** Le top 10 des espèces représentait **52,8 %** de
tous les runs — *Lolium perenne* à lui seul en pesait 27 951. Traiter chaque espèce comme
un « 1 » jette l'essentiel de l'information ; sortez toujours la version pondérée en
parallèle.

**Les organismes modèles polluent les listes.** *Arabidopsis thaliana*, *Brachypodium
distachyon*, *Spirodela polyrhiza* apparaîtront en tête. Ils ne sont « sombres » que par
artefact d'appariement de noms — excluez-les explicitement.

## Utilisation

```bash
python scripts/find_spectra.py --species "Banisteriopsis harleyi" --min-datasets 2
python scripts/find_spectra.py --file especes.txt --out fichiers.json
```
