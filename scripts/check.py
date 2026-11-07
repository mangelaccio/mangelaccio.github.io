#!/usr/bin/env python3
"""
Controllo pre-pubblicazione del sito.
Uso:  python scripts/check.py        (dalla cartella principale del repository)

Verifica che:
  - i file JSON in data/ siano sintatticamente validi
  - ogni voce abbia i campi obbligatori
  - i link locali (docs/..., img/...) puntino a file esistenti
Esce con codice 1 se trova errori: il workflow GitHub si ferma e NON pubblica.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors, warnings = [], []


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"{path.relative_to(ROOT)}: JSON non valido — riga {e.lineno}, colonna {e.colno}: {e.msg}")
    except FileNotFoundError:
        errors.append(f"{path.relative_to(ROOT)}: file mancante")
    return None


def is_placeholder(s):
    return isinstance(s, str) and "[" in s and "]" in s


def check_local_link(url, where):
    if not url or url.startswith(("http://", "https://", "mailto:", "#")):
        return
    if is_placeholder(url):
        warnings.append(f"{where}: link segnaposto ancora da compilare ({url})")
        return
    if not (ROOT / url).exists():
        errors.append(f"{where}: il file '{url}' non esiste nel repository")


def check_text(value, field, where):
    if value is None or value == "":
        errors.append(f"{where}: campo '{field}' mancante")
    elif isinstance(value, dict):
        if not (value.get("it") or value.get("en")):
            errors.append(f"{where}: campo '{field}' deve avere almeno 'it' o 'en'")
    elif not isinstance(value, (str, int)):
        errors.append(f"{where}: campo '{field}' deve essere una stringa o un oggetto {{it, en}}")


# ---- progetti ----
projects = load(ROOT / "data" / "projects.json")
if projects is not None:
    if not isinstance(projects, list):
        errors.append("projects.json: deve essere una lista [...]")
    else:
        ids = set()
        for i, p in enumerate(projects, 1):
            where = f"projects.json voce {i} ({p.get('title', '?')})"
            check_text(p.get("title"), "title", where)
            check_text(p.get("description"), "description", where)
            if p.get("id") in ids:
                errors.append(f"{where}: id duplicato '{p['id']}'")
            ids.add(p.get("id"))
            check_local_link(p.get("url", ""), where)

# ---- pubblicazioni ----
pubs = load(ROOT / "data" / "publications.json")
VALID_TYPES = {"article", "book", "report", "chapter", "other"}
if pubs is not None:
    if not isinstance(pubs, list):
        errors.append("publications.json: deve essere una lista [...]")
    else:
        for i, p in enumerate(pubs, 1):
            where = f"publications.json voce {i} ({p.get('title', '?')})"
            check_text(p.get("title"), "title", where)
            if not isinstance(p.get("year"), int):
                errors.append(f"{where}: 'year' deve essere un numero intero (es. 2026)")
            if p.get("type") not in VALID_TYPES:
                errors.append(f"{where}: 'type' deve essere uno tra {sorted(VALID_TYPES)}")
            check_local_link(p.get("url", ""), where)

# ---- file base ----
for required in ["index.html", "img/studio-outdoor-1.jpg", "img/studio-outdoor-2.jpg"]:
    if not (ROOT / required).exists():
        errors.append(f"file richiesto mancante: {required}")

# ---- esito ----
for w in warnings:
    print(f"  AVVISO  {w}")
for e in errors:
    print(f"  ERRORE  {e}")
if errors:
    print(f"\n{len(errors)} errore/i: correggi prima di pubblicare.")
    sys.exit(1)
print(f"\nOK — {len(projects or [])} progetti, {len(pubs or [])} pubblicazioni, {len(warnings)} avvisi.")
