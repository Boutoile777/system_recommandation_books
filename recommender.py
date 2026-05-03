"""Recommandation académique simple : TF–IDF + similarité cosinus sur le texte métadonnées."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


DATA = Path(__file__).resolve().parent / "data" / "books.csv"


class LivreRecommender:
    def __init__(self, csv_path: Path | None = None) -> None:
        chemin = csv_path or DATA
        self.df = pd.read_csv(chemin, encoding="utf-8")
        self.df["id"] = self.df["id"].astype(int)
        if "couverture_url" not in self.df.columns:
            self.df["couverture_url"] = ""

        vect = TfidfVectorizer(
            min_df=1,
            max_features=4000,
            ngram_range=(1, 2),
            stop_words=None,
        )
        corpus = (
            self.df["titre"].fillna("").astype(str)
            + " "
            + self.df["auteur"].fillna("").astype(str)
            + " "
            + self.df["genre"].fillna("").astype(str)
            + " "
            + self.df["description"].fillna("").astype(str)
        )
        self._X = vect.fit_transform(corpus)
        self._vect = vect

    @staticmethod
    def ligne_propre(series: pd.Series) -> dict:
        d = series.to_dict()
        out = {}
        for k, v in d.items():
            if v is None or (isinstance(v, float) and np.isnan(v)):
                out[k] = None
            elif hasattr(v, "item"):
                out[k] = v.item()
            else:
                out[k] = v
        if out.get("annee") is None:
            out["annee"] = ""
        cu = out.get("couverture_url")
        out["couverture_url"] = str(cu) if cu else ""
        return out

    def tous(self) -> list[dict]:
        return [self.ligne_propre(self.df.iloc[i]) for i in range(len(self.df))]

    def par_id(self, book_id: int) -> dict | None:
        s = self.df[self.df["id"] == book_id]
        return None if s.empty else self.ligne_propre(s.iloc[0])

    def genres_distincts(self) -> list[str]:
        return sorted(self.df["genre"].dropna().unique().tolist(), key=str.casefold)

    def filtrer(
        self,
        *,
        q_general: str = "",
        genre: str | None = None,
        auteur: str = "",
        annee: int | None = None,
    ) -> pd.DataFrame:
        """Filtres combinés : texte libre sur titre/auteur/genre, auteur précis, année exacte, genre."""
        d = self.df.copy()
        if genre and genre not in ("(tous)", ""):
            d = d[d["genre"].astype(str).str.casefold() == str(genre).casefold()]
        au = (auteur or "").strip().lower()
        if au:
            d = d[d["auteur"].str.lower().str.contains(au, na=False, regex=False)]
        if annee is not None:
            num = pd.to_numeric(d["annee"], errors="coerce")
            d = d[num.fillna(0).astype(int) == int(annee)]
        q = (q_general or "").strip().lower()
        if q:
            m = (
                d["titre"].str.lower().str.contains(q, na=False, regex=False)
                | d["auteur"].str.lower().str.contains(q, na=False, regex=False)
                | d["genre"].str.lower().str.contains(q, na=False, regex=False)
                | d["description"].fillna("").astype(str).str.lower().str.contains(q, na=False, regex=False)
            )
            d = d[m]
        return d

    def annees_disponibles(self) -> list[int]:
        out: list[int] = []
        for x in self.df["annee"].dropna().unique():
            try:
                y = int(float(x))
                if y > 0:
                    out.append(y)
            except (TypeError, ValueError):
                continue
        return sorted(set(out))

    def recommander(self, book_id: int, k: int = 6) -> list[tuple[dict, float]]:
        idx = self.df.index[self.df["id"] == book_id]
        if idx.empty:
            return []
        i = int(idx[0])
        sims = linear_kernel(self._X[i], self._X).flatten()
        pairs = [(j, float(sims[j])) for j in range(len(self.df)) if j != i]
        pairs.sort(key=lambda x: x[1], reverse=True)
        top = pairs[: max(1, min(k, 30))]
        return [(self.ligne_propre(self.df.iloc[j]), sc) for j, sc in top]
