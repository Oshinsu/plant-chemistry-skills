#!/usr/bin/env python3
"""Tests des pièges connus. Chaque cas vient d'une erreur réellement commise.

Ces tests ne vérifient pas que le code s'exécute : ils vérifient qu'il attrape
les pièges qui ont produit de faux résultats en production.

Usage :
    python tests/test_traps.py --wcvp /chemin/wcvp_names.csv        # hors ligne
    python tests/test_traps.py --wcvp ... --online                  # + Wikidata
"""

import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- pièges de nomenclature : nom cherché -> nom accepté attendu -----------
# Chacun a réellement fait disparaître de la chimie dans une analyse publiée.
NAME_TRAPS = [
    ("Vetiveria zizanioides", "Chrysopogon zizanioides"),   # genre fusionné
    ("Wedelia trilobata", "Sphagneticola trilobata"),       # genre reclassé
    ("Chamaesyce hirta", "Euphorbia hirta"),                # genre reclassé
    ("Eucalyptus citriodora", "Corymbia citriodora"),       # genre reclassé
    ("Ocimum sanctum", "Ocimum tenuiflorum"),               # synonyme simple
    ("Hyptis verticillata", "Condea verticillata"),         # genre éclaté
]

# --- normalisation : variantes qui doivent s'apparier ---------------------
NORM_EQUIV = [
    ("Citrus × limon", "Citrus x limon"),                   # signe multiplié vs x
    ("Citrus × limon", "Citrus limon"),                     # hybride vs simple
    ("Raphanus raphanistrum subsp. sativus", "Raphanus raphanistrum"),
    ("Pimenta  racemosa", "Pimenta racemosa"),              # espaces multiples
]


def test_names(wcvp_path):
    mod = load(ROOT / "skills" / "wcvp-name-resolution" / "scripts" / "resolve.py",
               "resolve")
    print("Normalisation")
    ok = True
    for a, b in NORM_EQUIV:
        same = mod.normalise(a) == mod.normalise(b)
        print(f"  [{'OK   ' if same else 'ÉCHEC'}] {a!r} == {b!r}")
        ok &= same

    print("\nRésolution des pièges de genre")
    print("  chargement de WCVP...")
    exact, norm_sp, norm_any, acc_meta, _syn = mod.load_wcvp(wcvp_path)
    for name, expected in NAME_TRAPS:
        acc, how = mod.resolve_one(name, exact, norm_sp, norm_any)
        got = acc_meta.get(acc, {}).get("accepted_name") if acc else None
        good = got == expected
        print(f"  [{'OK   ' if good else 'ÉCHEC'}] {name:<26} -> "
              f"{got or 'NON RÉSOLU'}"
              f"{'' if good else f'   (attendu {expected})'}   [{how}]")
        ok &= good
    return ok


def test_chemistry():
    mod = load(ROOT / "skills" / "lotus-chemistry-lookup" / "scripts" / "lookup.py",
               "lookup")
    print("\nGarde-fou des témoins")
    got = mod.species_counts(list(mod.GOLDEN))
    ok = True
    for name, floor in mod.GOLDEN.items():
        n = got.get(name, 0)
        good = n >= floor
        print(f"  [{'OK   ' if good else 'ÉCHEC'}] {name:<24} {n:>5} "
              f"(plancher {floor})")
        ok &= good

    print("\nGenre : la traversée P171 doit trouver ce que P703-direct rate")
    res = mod.genus_counts(["Buxus", "Vanilla"])
    for g in ("Buxus", "Vanilla"):
        n = res[g]["compounds"]
        good = n > 0
        print(f"  [{'OK   ' if good else 'ÉCHEC'}] genre {g:<12} {n:>5} composés "
              f"/ {res[g]['child_species']} espèces")
        ok &= good
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wcvp", required=True)
    ap.add_argument("--online", action="store_true",
                    help="exécuter aussi les tests qui interrogent Wikidata")
    args = ap.parse_args()

    ok = test_names(args.wcvp)
    if args.online:
        ok &= test_chemistry()
    else:
        print("\n(tests Wikidata ignorés — relancer avec --online)")

    print("\n" + ("TOUS LES TESTS PASSENT" if ok else "DES TESTS ÉCHOUENT"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
