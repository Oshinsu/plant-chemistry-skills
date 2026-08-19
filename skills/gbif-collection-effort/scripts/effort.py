#!/usr/bin/env python3
"""Mesure l'effort de collecte GBIF — par espèce ou par territoire.

L'effort de collecte est presque toujours le facteur dominant dans les analyses
de couverture. Ce script produit la covariable de contrôle, et dédoublonne les
clés GBIF multiples qui contaminent les listes d'espèces rares.

Usage :
    python effort.py --names "Inga martinicensis" "Hyptis atrorubens"
    python effort.py --file noms.txt --out effort.json
    python effort.py --country MQ --checklist --out flore_mq.json
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

GBIF = "https://api.gbif.org/v1"
HEADERS = {"User-Agent": "plant-chemistry-skills/1.0 (recherche; contact requis)"}
TRACHEOPHYTA = 7707728


def get(url, **params):
    for _ in range(4):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=90)
            if r.status_code == 200:
                return r.json()
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2)
    return None


def species_effort(name):
    """Occurrences mondiales d'une espèce : le proxy d'effort de collecte."""
    m = get(f"{GBIF}/species/match", name=name, kingdom="Plantae")
    if not m or m.get("matchType") == "NONE":
        return {"name": name, "matched": None, "key": None,
                "world_occurrences": 0, "n_countries": None}
    key = m.get("usageKey")
    occ = get(f"{GBIF}/occurrence/search", speciesKey=key, limit=0) or {}
    fac = get(f"{GBIF}/occurrence/search", speciesKey=key, limit=0,
              facet="country", facetLimit=300) or {}
    facets = fac.get("facets") or []
    return {
        "name": name,
        "matched": m.get("canonicalName"),
        "status": m.get("status"),
        "key": key,
        "family": m.get("family"),
        "genus": m.get("genus"),
        "world_occurrences": occ.get("count", 0),
        # ATTENTION : nombre de pays != aire de répartition. Voir SKILL.md.
        "n_countries": len(facets[0]["counts"]) if facets else 0,
    }


def territory_checklist(country):
    """Inventaire des plantes vasculaires d'un territoire, avec occurrences locales."""
    d = get(f"{GBIF}/occurrence/search", country=country, taxonKey=TRACHEOPHYTA,
            limit=0, facet="speciesKey", facetLimit=6000)
    if not d or not d.get("facets"):
        return [], 0
    counts = {c["name"]: c["count"] for c in d["facets"][0]["counts"]}
    total = d.get("count", 0)
    print(f"  {len(counts)} espèces, {total} occurrences", file=sys.stderr)

    def resolve(item):
        key, n = item
        s = get(f"{GBIF}/species/{key}") or {}
        return {"key": key, "name": s.get("canonicalName"),
                "family": s.get("family"), "genus": s.get("genus"),
                "rank": s.get("rank"), "local_occurrences": n}

    with ThreadPoolExecutor(max_workers=8) as pool:
        recs = list(pool.map(resolve, counts.items()))
    return [r for r in recs if r.get("name") and r.get("rank") == "SPECIES"], total


def dedupe_by_name(records, effort_field="world_occurrences"):
    """Un nom = une ligne. 47 noms sur 3 780 portaient plusieurs clés GBIF,
    et la clé secondaire est systématiquement la plus étroite : sans
    dédoublonnage elle contamine toute liste d'espèces à faible étendue."""
    best = {}
    for r in records:
        nm = r.get("name")
        if not nm:
            continue
        if nm not in best or (r.get(effort_field) or 0) > (best[nm].get(effort_field) or 0):
            best[nm] = r
    removed = len(records) - len(best)
    if removed:
        print(f"  {removed} doublons de clés GBIF retirés", file=sys.stderr)
    return list(best.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", nargs="*", default=[])
    ap.add_argument("--file")
    ap.add_argument("--country", help="code pays ISO, ex. MQ")
    ap.add_argument("--checklist", action="store_true",
                    help="inventaire complet du territoire")
    ap.add_argument("--out")
    args = ap.parse_args()

    if args.checklist:
        if not args.country:
            ap.error("--checklist exige --country")
        print(f"Inventaire des plantes vasculaires : {args.country}", file=sys.stderr)
        recs, total = territory_checklist(args.country)
        recs = dedupe_by_name(recs, "local_occurrences")
        payload = {"country": args.country, "n_species": len(recs),
                   "n_occurrences": total, "species": recs,
                   "warning": ("Cet inventaire mêle flore spontanée, introduite et "
                               "cultivée. establishmentMeans est quasi vide dans GBIF "
                               "et ne permet pas de les séparer.")}
    else:
        names = list(args.names)
        if args.file:
            with open(args.file, encoding="utf-8") as fh:
                names += [l.strip() for l in fh if l.strip()]
        if not names:
            ap.error("fournir --names, --file, ou --checklist avec --country")
        print(f"Effort de collecte pour {len(names)} espèces", file=sys.stderr)
        with ThreadPoolExecutor(max_workers=8) as pool:
            recs = list(pool.map(species_effort, names))
        got = [r for r in recs if r["world_occurrences"] > 0]
        if got:
            occ = sorted(r["world_occurrences"] for r in got)
            print(f"  {len(got)}/{len(recs)} avec occurrences", file=sys.stderr)
            print(f"  médiane {occ[len(occ)//2]}, min {occ[0]}, max {occ[-1]}",
                  file=sys.stderr)
        payload = {"n_species": len(recs), "species": recs,
                   "warning": ("n_countries est un proxy d'exposition, PAS une aire "
                               "de répartition (corrélation 0,846 avec l'effort). "
                               "Pour l'aire, utiliser WCVP.")}

    text = json.dumps(payload, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"écrit -> {args.out}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
