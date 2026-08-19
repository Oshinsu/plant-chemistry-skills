#!/usr/bin/env python3
"""Résout des noms de plantes contre WCVP et les étend à tous leurs synonymes.

WCVP (World Checklist of Vascular Plants, Royal Botanic Gardens Kew) est la
nomenclature de référence. Archive publique, CC BY 4.0 :
    https://sftp.kew.org/pub/data-repositories/WCVP/wcvp.zip

Usage :
    python resolve.py --wcvp wcvp_names.csv --names "Vetiveria zizanioides" ...
    python resolve.py --wcvp wcvp_names.csv --file noms.txt --out resolus.json

Sortie JSON : un objet par nom d'entrée, avec la liste complète des noms de
recherche à utiliser en aval, et un bloc de contrôle qualité à publier avec
tout résultat.
"""

import argparse
import csv
import json
import re
import sys
from collections import defaultdict

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

HYBRID = "×"


def normalise(name):
    """Clé de comparaison tolérante : hybrides, rangs infraspécifiques, espaces.

    ATTENTION : cette clé est volontairement permissive et fait collisionner
    « Genus species » avec « Genus species var. x ». Elle ne doit servir qu'en
    DERNIER RECOURS — voir resolve_one() pour l'ordre de priorité.
    """
    s = (name or "").strip().replace(HYBRID, "x").replace("✕", "x")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\bx\s+", "", s)                        # marqueur hybride
    s = re.sub(r"\s+(subsp|var|f|ssp)\.?\s+\S+", "", s)  # rang infraspécifique
    return s.lower().strip()


def load_wcvp(path):
    """Charge WCVP en trois index : exact, normalisé-espèce, normalisé-tous rangs."""
    exact = {}                       # nom exact -> (acc_id, rank, status)
    norm_species = defaultdict(list)  # clé normalisée -> entrées de rang Species
    norm_any = defaultdict(list)      # clé normalisée -> toutes entrées
    acc_meta = {}                     # acc_id -> métadonnées du taxon accepté
    synonyms = defaultdict(set)       # acc_id -> tous les noms qui y pointent

    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="|"):
            rank = row["taxon_rank"]
            if rank not in ("Species", "Subspecies", "Variety", "Form"):
                continue
            name = row["taxon_name"]
            acc = row["accepted_plant_name_id"]
            status = row["taxon_status"]
            if not name:
                continue

            entry = (acc, rank, status)
            if name not in exact or status == "Accepted":
                exact[name] = entry
            n = normalise(name)
            if rank == "Species":
                norm_species[n].append(entry)
            norm_any[n].append(entry)

            if status == "Accepted" and row["plant_name_id"] == acc:
                acc_meta[acc] = {"accepted_name": name, "family": row["family"],
                                 "genus": row["genus"], "rank": rank,
                                 "lifeform": row.get("lifeform_description", "")}
            if acc:
                synonyms[acc].add(name)

    return exact, norm_species, norm_any, acc_meta, synonyms


def pick(entries):
    """Parmi plusieurs entrées, préférer un statut Accepted, puis le rang Species."""
    if not entries:
        return None
    for acc, rank, status in entries:
        if status == "Accepted" and rank == "Species" and acc:
            return acc
    for acc, rank, status in entries:
        if rank == "Species" and acc:
            return acc
    for acc, _rank, _status in entries:
        if acc:
            return acc
    return None


def resolve_one(name, exact, norm_species, norm_any):
    """Ordre de priorité strict, du plus sûr au plus permissif.

    1. correspondance EXACTE — toujours préférée
    2. correspondance normalisée parmi les seuls taxons de rang Species
    3. correspondance normalisée tous rangs confondus

    Sans cet ordre, une variété synonyme d'une AUTRE espèce peut détourner la
    résolution : « Vetiveria zizanioides » se résolvait ainsi à tort en
    « Chrysopogon argutus » au lieu de « Chrysopogon zizanioides ».
    """
    if name in exact:
        acc = exact[name][0]
        if acc:
            return acc, "exact"
    n = normalise(name)
    acc = pick(norm_species.get(n, []))
    if acc:
        return acc, "normalise_espece"
    acc = pick(norm_any.get(n, []))
    if acc:
        return acc, "normalise_tous_rangs"
    return None, "non_resolu"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wcvp", required=True, help="chemin vers wcvp_names.csv")
    ap.add_argument("--names", nargs="*", default=[])
    ap.add_argument("--file", help="fichier texte, un nom par ligne")
    ap.add_argument("--out")
    args = ap.parse_args()

    names = list(args.names)
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            names += [l.strip() for l in fh if l.strip()]
    if not names:
        ap.error("fournir --names ou --file")

    print(f"{len(names)} noms en entrée", file=sys.stderr)
    print("chargement de WCVP...", file=sys.stderr)
    exact, norm_species, norm_any, acc_meta, synonyms = load_wcvp(args.wcvp)

    out = []
    for original in names:
        acc, how = resolve_one(original, exact, norm_species, norm_any)
        meta = acc_meta.get(acc, {}) if acc else {}
        search = {original}
        if meta.get("accepted_name"):
            search.add(meta["accepted_name"])
        if acc:
            search |= synonyms.get(acc, set())
        accepted = meta.get("accepted_name")
        out.append({
            "input": original,
            "resolved": bool(acc),
            "match_type": how,
            "accepted_name": accepted,
            "wcvp_id": acc,
            "family": meta.get("family"),
            "genus": meta.get("genus"),
            "lifeform": meta.get("lifeform"),
            "is_synonym": bool(accepted and normalise(accepted) != normalise(original)),
            "search_names": sorted(search),
        })

    n_res = sum(1 for r in out if r["resolved"])
    n_syn = sum(1 for r in out if r["is_synonym"])
    n_search = sum(len(r["search_names"]) for r in out)
    unresolved = [r["input"] for r in out if not r["resolved"]]
    by_type = defaultdict(int)
    for r in out:
        by_type[r["match_type"]] += 1

    print(f"résolus            : {n_res}/{len(out)} "
          f"({100*n_res/len(out):.1f} %)", file=sys.stderr)
    for k, v in sorted(by_type.items()):
        print(f"  {k:<22} {v}", file=sys.stderr)
    print(f"synonymes détectés : {n_syn}", file=sys.stderr)
    print(f"noms de recherche  : {n_search} "
          f"(moyenne {n_search/max(len(out),1):.1f} par entrée)", file=sys.stderr)
    if unresolved:
        print(f"NON RÉSOLUS ({len(unresolved)}) : "
              f"{', '.join(unresolved[:8])}", file=sys.stderr)
    fallback = by_type.get("normalise_tous_rangs", 0)
    if fallback:
        print(f"ATTENTION : {fallback} résolus par la voie la plus permissive — "
              f"à vérifier à la main", file=sys.stderr)

    payload = {
        "quality": {"n_input": len(out), "n_resolved": n_res, "n_synonyms": n_syn,
                    "n_search_names": n_search, "match_types": dict(by_type),
                    "unresolved": unresolved},
        "taxa": out,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"écrit -> {args.out}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
