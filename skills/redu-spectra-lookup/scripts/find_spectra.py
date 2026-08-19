#!/usr/bin/env python3
"""Trouve les fichiers de spectres publics d'une liste d'espèces (Pan-ReDU).

Lit le dump ReDU en flux pour ne pas stocker 844 Mo, et filtre sur les espèces
cibles. Donne la correspondance fichier par fichier — nécessaire parce que les
jeux de données sont souvent des plaques multi-espèces.

Usage :
    python find_spectra.py --species "Banisteriopsis harleyi" --min-datasets 2
    python find_spectra.py --file especes.txt --out fichiers.json
"""

import argparse
import json
import re
import sys
from collections import defaultdict

import requests

DUMP = "https://redu.gnps2.org/dump"
CACHE = "https://datasetcache.gnps2.org/datasette/database/filename.json"
HEADERS = {"User-Agent": "plant-chemistry-skills/1.0 (recherche; contact requis)"}

# Organismes modèles et cultures : ils dominent les dépôts et ne sont
# « inexplorés » que par artefact d'appariement de noms.
MODEL_ORGANISMS = {
    "Arabidopsis thaliana", "Oryza sativa", "Zea mays", "Solanum lycopersicum",
    "Brachypodium distachyon", "Spirodela polyrhiza", "Medicago truncatula",
    "Nicotiana tabacum", "Nicotiana benthamiana", "Glycine max",
    "Triticum aestivum", "Hordeum vulgare", "Lolium perenne",
    "Chlamydomonas reinhardtii", "Physcomitrium patens",
}


def stream_redu(targets):
    """Lit le dump en flux, retient les lignes des espèces cibles."""
    r = requests.get(DUMP, stream=True, timeout=1800, headers=HEADERS)
    r.raise_for_status()

    header, idx, hits, n = None, {}, defaultdict(list), 0
    for raw in r.iter_lines(decode_unicode=True):
        if not raw:
            continue
        parts = raw.split("\t")
        if header is None:
            header = parts
            for col in ("ATTRIBUTE_DatasetAccession", "filename", "NCBITaxonomy",
                        "MassSpectrometer", "IonizationSourceAndPolarity",
                        "ChromatographyAndPhase"):
                if col in header:
                    idx[col] = header.index(col)
            missing = {"ATTRIBUTE_DatasetAccession", "filename",
                       "NCBITaxonomy"} - set(idx)
            if missing:
                sys.exit(f"colonnes manquantes dans le dump : {missing}")
            continue
        n += 1
        if n % 250000 == 0:
            print(f"  {n} lignes lues, "
                  f"{sum(len(v) for v in hits.values())} fichiers retenus",
                  file=sys.stderr)
        try:
            tax = parts[idx["NCBITaxonomy"]]
        except IndexError:
            continue
        if not tax or tax == "missing value":
            continue
        m = re.match(r"^\d+\|(.+)$", tax)          # format "3816|Abrus precatorius"
        sp = (m.group(1) if m else tax).strip()
        if sp not in targets:
            continue
        try:
            hits[sp].append({
                "dataset": parts[idx["ATTRIBUTE_DatasetAccession"]],
                "filename": parts[idx["filename"]],
                "instrument": parts[idx["MassSpectrometer"]] if "MassSpectrometer" in idx else "",
                "ionisation": parts[idx["IonizationSourceAndPolarity"]] if "IonizationSourceAndPolarity" in idx else "",
            })
        except IndexError:
            continue
    print(f"  {n} lignes lues au total", file=sys.stderr)
    return hits


def file_details(dataset):
    """Tailles et comptages de spectres par fichier, via le cache GNPS2."""
    try:
        r = requests.get(CACHE, params={"dataset__exact": dataset, "_size": 500},
                         headers=HEADERS, timeout=120)
        if r.status_code != 200:
            return {}
        d = r.json()
        cols = d["columns"]
        return {row[cols.index("filepath")]: {
            "size_mb": row[cols.index("size_mb")],
            "ms2": row[cols.index("spectra_ms2")],
            "instrument": row[cols.index("instrument_model")],
        } for row in d["rows"]}
    except Exception:  # noqa: BLE001
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--species", nargs="*", default=[])
    ap.add_argument("--file", help="fichier texte, un nom par ligne")
    ap.add_argument("--min-datasets", type=int, default=2,
                    help="seuil de robustesse (défaut 2 : une espèce vue dans un "
                         "seul jeu est l'artefact d'un seul laboratoire)")
    ap.add_argument("--keep-models", action="store_true",
                    help="ne pas exclure les organismes modèles et cultures")
    ap.add_argument("--details", action="store_true",
                    help="récupérer tailles et comptages MS2 (plus lent)")
    ap.add_argument("--out")
    args = ap.parse_args()

    names = list(args.species)
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            names += [l.strip() for l in fh if l.strip()]
    if not names:
        ap.error("fournir --species ou --file")

    targets = set(names)
    if not args.keep_models:
        excluded = targets & MODEL_ORGANISMS
        targets -= MODEL_ORGANISMS
        if excluded:
            print(f"organismes modèles exclus : {', '.join(sorted(excluded))}",
                  file=sys.stderr)

    print(f"recherche de {len(targets)} espèces dans le dump ReDU", file=sys.stderr)
    hits = stream_redu(targets)

    out = {}
    for sp, entries in hits.items():
        datasets = {e["dataset"] for e in entries}
        if len(datasets) < args.min_datasets:
            continue
        rec = {"n_files": len(entries), "n_datasets": len(datasets),
               "datasets": sorted(datasets), "files": entries}
        if args.details:
            det = {}
            for ds in sorted(datasets):
                det.update(file_details(ds))
            for e in rec["files"]:
                key = e["filename"][2:] if e["filename"].startswith("f.") else e["filename"]
                if key in det:
                    e.update(det[key])
        out[sp] = rec

    print(f"\n{len(hits)}/{len(targets)} espèces trouvées dans les dépôts",
          file=sys.stderr)
    print(f"{len(out)} passent le seuil de {args.min_datasets} jeux indépendants",
          file=sys.stderr)
    for sp, r in sorted(out.items(), key=lambda kv: -kv[1]["n_files"])[:15]:
        print(f"  {sp:<40} {r['n_files']:>4} fichiers, "
              f"{r['n_datasets']} jeux", file=sys.stderr)

    payload = {"min_datasets": args.min_datasets, "n_species": len(out),
               "species": out,
               "note": ("Présence de spectres = un signal a été enregistré, "
                        "PAS une molécule identifiée.")}
    text = json.dumps(payload, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"écrit -> {args.out}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
