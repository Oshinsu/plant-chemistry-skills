#!/usr/bin/env python3
"""Interroge LOTUS (via Wikidata P703) pour la chimie décrite d'un taxon.

Comporte un garde-fou bloquant : la requête doit retrouver la chimie de taxons
massivement publiés, sinon le script s'arrête. Ce garde-fou a réellement
intercepté un bug qui faisait conclure que le genre Buxus n'avait aucun composé
décrit.

Usage :
    python lookup.py --names "Inga martinicensis" "Hyptis atrorubens"
    python lookup.py --file noms.txt --level genus --out chimie.json
    python lookup.py --names Buxus --level genus      # traverse P171
"""

import argparse
import json
import sys
import time

import requests

ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {
    "User-Agent": "plant-chemistry-skills/1.0 (recherche; contact requis)",
    "Accept": "application/sparql-results+json",
}

# Témoins : espèces dont la chimie est massivement publiée.
# Si l'un revient sous son plancher, la requête est cassée.
GOLDEN = {
    "Catharanthus roseus": 100,
    "Coffea arabica": 50,
    "Buxus sempervirens": 30,
    "Vanilla planifolia": 20,
}


def sparql(query, tries=6):
    for attempt in range(tries):
        try:
            r = requests.post(ENDPOINT, data={"query": query},
                              headers=HEADERS, timeout=300)
            if r.status_code == 200:
                return r.json()["results"]["bindings"]
            print(f"  [essai {attempt+1}] HTTP {r.status_code}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            print(f"  [essai {attempt+1}] {type(exc).__name__}", file=sys.stderr)
        time.sleep(4 * (attempt + 1))
    raise RuntimeError("requête SPARQL échouée après plusieurs essais")


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def species_counts(names, batch=50):
    """Composés distincts rattachés directement à chaque nom d'espèce."""
    found = {}
    batches = list(chunks(sorted(set(names)), batch))
    for i, b in enumerate(batches, 1):
        values = " ".join('"%s"' % n.replace('"', "") for n in b)
        q = f"""
        SELECT ?name (COUNT(DISTINCT ?c) AS ?n) WHERE {{
          VALUES ?name {{ {values} }}
          ?taxon wdt:P225 ?name .
          OPTIONAL {{ ?c wdt:P703 ?taxon . }}
        }}
        GROUP BY ?name
        """
        for row in sparql(q):
            nm = row["name"]["value"]
            found[nm] = max(found.get(nm, 0), int(row["n"]["value"]))
        if i % 10 == 0 or i == len(batches):
            print(f"  lot {i}/{len(batches)}", file=sys.stderr)
        time.sleep(0.7)
    return found


def genus_counts(genera):
    """Composés dans TOUTE espèce fille du genre.

    Compter P703 sur l'item genre lui-même renvoie presque toujours zéro :
    LOTUS rattache les composés aux items espèce. Il faut traverser P171.
    """
    out = {}
    for i, g in enumerate(sorted(set(genera)), 1):
        q = f"""
        SELECT (COUNT(DISTINCT ?c) AS ?nc) (COUNT(DISTINCT ?sp) AS ?nsp) WHERE {{
          ?genus wdt:P225 "{g}" ; wdt:P105 wd:Q34740 .
          ?sp wdt:P171 ?genus .
          OPTIONAL {{ ?c wdt:P703 ?sp . }}
        }}
        """
        rows = sparql(q)
        out[g] = {
            "compounds": int(rows[0]["nc"]["value"]) if rows else 0,
            "child_species": int(rows[0]["nsp"]["value"]) if rows else 0,
        }
        print(f"  genre {i}/{len(set(genera))} : {g} -> "
              f"{out[g]['compounds']} composés / {out[g]['child_species']} espèces",
              file=sys.stderr)
        time.sleep(0.5)
    return out


def validate():
    """Refuse de continuer si la requête ne retrouve pas les témoins."""
    print("Garde-fou : témoins massivement publiés", file=sys.stderr)
    got = species_counts(list(GOLDEN))
    ok = True
    for name, floor in GOLDEN.items():
        n = got.get(name, 0)
        status = "OK   " if n >= floor else "ÉCHEC"
        if n < floor:
            ok = False
        print(f"  [{status}] {name:<24} {n:>5} composés "
              f"(plancher {floor})", file=sys.stderr)
    if not ok:
        sys.exit("ARRÊT : la requête ne retrouve pas la chimie de taxons connus. "
                 "Aucun chiffre de ce script n'est publiable en l'état.")
    print("  -> requête validée\n", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", nargs="*", default=[])
    ap.add_argument("--file", help="fichier texte, un nom par ligne")
    ap.add_argument("--level", choices=["species", "genus"], default="species")
    ap.add_argument("--out")
    ap.add_argument("--skip-validation", action="store_true",
                    help="À N'UTILISER QUE POUR DÉBOGUER, jamais pour publier")
    args = ap.parse_args()

    names = list(args.names)
    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            names += [l.strip() for l in fh if l.strip()]
    if not names:
        ap.error("fournir --names ou --file")

    if not args.skip_validation:
        validate()

    if args.level == "genus":
        result = genus_counts(names)
        zero = [g for g, v in result.items() if v["compounds"] == 0]
        payload = {"level": "genus", "results": result, "zero_genera": zero}
        print(f"\n{len(zero)}/{len(result)} genres sans aucun composé",
              file=sys.stderr)
    else:
        counts = species_counts(names)
        zero = [n for n in names if counts.get(n, 0) == 0]
        absent = [n for n in names if n not in counts]
        payload = {
            "level": "species",
            "counts": {n: counts.get(n, 0) for n in names},
            "zero": zero,
            "absent_from_wikidata": absent,
            "note": ("« zéro » signifie absent des corpus machine-lisibles, "
                     "PAS jamais étudié. Les espèces absentes de Wikidata "
                     "valent zéro par construction, pas par mesure."),
        }
        print(f"\n{len(zero)}/{len(names)} sans composé décrit", file=sys.stderr)
        print(f"{len(absent)} absents de Wikidata "
              f"(zéro par construction)", file=sys.stderr)

    text = json.dumps(payload, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"écrit -> {args.out}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
