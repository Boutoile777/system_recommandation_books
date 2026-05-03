"""
Télécharge ~200 livres profil variés depuis Open Library (couvertures obligatoires).

Usage :
  cd <racine_du_projet>
  .venv\\Scripts\\python scripts/fetch_books_ol.py
"""

from __future__ import annotations

import csv
import math
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.exceptions import ProtocolError
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "books.csv"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Sujets variés pour mélanger périodes, styles et genres (libellés utilisés comme « genre » affiché)
SUBJECTS = [
    "fiction",
    "romance",
    "science_fiction",
    "fantasy",
    "mystery_and_detective_stories",
    "young_adult_fiction",
    "thrillers",
    "juvenile_fiction",
    "biography",
    "history",
    "horror_stories",
    "poetry",
    "adventure_and_adventurers",
    "american_fiction",
    "translations",
]

TARGET = 200


def quota_par_sujet(n_sujets: int, cible: int) -> int:
    """Au moins ceil(cible/n) livres tentés par sujet avant de compléter."""
    return max(8, math.ceil(cible / max(1, n_sujets)) + 2)


def couverture_depuis_work(work: dict) -> str | None:
    cid = work.get("cover_id") or work.get("cover_i")
    cov = work.get("covers") or []
    if cid is None and cov:
        try:
            cid = cov[0]
        except (IndexError, TypeError):
            cid = None
    if cid is None:
        return None
    try:
        return f"https://covers.openlibrary.org/b/id/{int(cid)}-M.jpg"
    except (TypeError, ValueError):
        return None


def ligne_auteurs(work: dict) -> str:
    noms = []
    for a in work.get("authors") or []:
        n = str(a.get("name") or "").strip()
        if n:
            noms.append(n)
    return ", ".join(noms[:4])[:400] if noms else "—"


def libelle_genre(subject_slug: str) -> str:
    return subject_slug.replace("_", " ").title()


def recuperer_sess() -> requests.Session:
    """
    Session avec retries urllib3 + petit pool (connexions parfois fermées brutalement par OL).
    """
    s = requests.Session()
    retry = Retry(
        total=10,
        connect=10,
        read=10,
        backoff_factor=1.8,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )
    # pool_maxsize=1 : moins de reuse d’une connexion HTTP half-dead (RemoteDisconnected).
    adapter = HTTPAdapter(max_retries=retry, pool_connections=1, pool_maxsize=1)
    s.mount("https://", adapter)
    s.headers.update(
        {
            "User-Agent": UA,
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "close",
        }
    )
    return s


def requete_json_get(
    sess: requests.Session,
    url: str,
    *,
    params: dict,
    timeout: tuple[float, float] = (15.0, 90.0),
) -> requests.Response | None:
    """GET avec tentatives manuelles en plus de celles de urllib3 (erreurs transport)."""
    derniere: Exception | None = None
    for k in range(7):
        try:
            r = sess.get(url, params=params, timeout=timeout)
            if r.status_code < 500:
                return r
            time.sleep(min(8.0, 1.5 * (2**k)))
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError,
            ProtocolError,
            OSError,
        ) as exc:
            derniere = exc
            time.sleep(min(10.0, 1.2 * (2**k)))
    if derniere is not None:
        raise derniere
    return None


def main() -> None:
    sess = recuperer_sess()
    vu: set[str] = set()
    lignes: list[dict] = []
    plafond_offset = 4000

    cap = quota_par_sujet(len(SUBJECTS), TARGET)
    compteur_sujet: dict[str, int] = {s: 0 for s in SUBJECTS}

    def ramasser_pour_sujet(sub: str, max_pour_ce_sujet: int) -> None:
        nonlocal lignes
        label = libelle_genre(sub)
        offset = 0
        while (
            len(lignes) < TARGET
            and compteur_sujet[sub] < max_pour_ce_sujet
            and offset < plafond_offset
        ):
            url = f"https://openlibrary.org/subjects/{sub}.json"
            params = {"limit": 50, "details": "true", "offset": offset}
            try:
                r = requete_json_get(sess, url, params=params)
            except OSError as e:
                print(f"[openlibrary] échec réseau sur {sub!r} offset={offset}: {e}")
                break
            if r is None or r.status_code >= 400:
                if r is not None and r.status_code != 404:
                    print(f"[openlibrary] HTTP {r.status_code} pour {sub!r} offset={offset}")
                break
            data = r.json()
            oeuvres = data.get("works") or []
            if not oeuvres:
                break

            avant = len(lignes)
            for w in oeuvres:
                if len(lignes) >= TARGET or compteur_sujet[sub] >= max_pour_ce_sujet:
                    break
                cle = str(w.get("key") or "")
                if not cle or cle in vu:
                    continue
                url_cover = couverture_depuis_work(w)
                if not url_cover:
                    continue
                vu.add(cle)
                an = w.get("first_publish_year")
                try:
                    annee_val: int | str = int(an) if an not in (None, "") else ""
                except (TypeError, ValueError):
                    annee_val = ""
                lignes.append(
                    {
                        "titre": (str(w.get("title") or "Sans titre").strip())[:500],
                        "auteur": ligne_auteurs(w),
                        "genre": label,
                        "annee": annee_val,
                        "description": "",
                        "couverture_url": url_cover,
                    }
                )
                compteur_sujet[sub] += 1

            offset += len(oeuvres)
            if not oeuvres:
                break
            # Délai plus long : OL ferme souvent les connexions si on enchaîne trop vite.
            time.sleep(0.28)

    # Phase 1 : diversité forte (quota par sujet)
    for sub in SUBJECTS:
        if len(lignes) >= TARGET:
            break
        ramasser_pour_sujet(sub, cap)

    # Phase 2 : compléter jusqu’à TARGET depuis les sujets les moins garnis
    if len(lignes) < TARGET:
        rotations = 0
        while len(lignes) < TARGET and rotations < 250:
            rotations += 1
            progressed = False
            for sub in SUBJECTS:
                if len(lignes) >= TARGET:
                    break
                avant = len(lignes)
                ramasser_pour_sujet(sub, 10**9)
                if len(lignes) > avant:
                    progressed = True
            if not progressed:
                break

    OUT.parent.mkdir(parents=True, exist_ok=True)
    cols = ["id", "titre", "auteur", "genre", "annee", "description", "couverture_url"]
    avec = lignes[:TARGET]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for i, ligne in enumerate(avec, start=1):
            row = {**ligne, "id": i}
            if row.get("annee") == "":
                row["annee"] = ""
            writer.writerow(row)

    print(f"{len(avec)} livres écrits dans {OUT}")
    if len(avec) < TARGET:
        print(f"Attention : seulement {len(avec)} entrées avec couverture (cible {TARGET}). Réessayez plus tard ou ajoutez des sujets dans SUBJECTS.")


if __name__ == "__main__":
    main()
