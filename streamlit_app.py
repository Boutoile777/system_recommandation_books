"""
Application Streamlit : Accueil (catalogue) · Mes bouquins (panier) · Ma sélection (reco).
"""

from __future__ import annotations

import math
from pathlib import Path

import streamlit as st

from recommender import LivreRecommender

# Incrémenter si la classe LivreRecommender change (invalide le cache Streamlit).
_MOTEUR_CODE_VERSION = 2
_DATA_CSV = Path(__file__).resolve().parent / "data" / "books.csv"

PAGE_SIZE = 20
COLS_GRID = 5
NB_VOISINS = 8  # nombre de suggestions fixe (non réglable par l'utilisateur)

NAV_LABELS = ("Accueil", "Mes bouquins", "Ma sélection")

st.set_page_config(
    page_title="Bibliothèque personnelle",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_animations_css() -> None:
    st.markdown(
        """
<style>
@keyframes vueFadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
section.main .block-container {
  animation: vueFadeIn 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}
section.main button {
  transition: transform 0.18s ease, box-shadow 0.22s ease, filter 0.2s ease !important;
}
section.main button:hover {
  filter: brightness(1.05);
}
section.main [data-testid="baseButton-primary"]:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(90, 120, 200, 0.35);
}
section.main [data-testid="stImage"] picture img,
section.main [data-testid="stImage"] img {
  border-radius: 10px;
  transition: transform 0.32s ease, box-shadow 0.32s ease !important;
  box-shadow: 0 3px 14px rgba(0, 0, 0, 0.14);
}
section.main [data-testid="stImage"]:hover picture img,
section.main [data-testid="stImage"]:hover img {
  transform: scale(1.045);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18) !important;
}
</style>
""",
        unsafe_allow_html=True,
    )


@st.cache_resource
def moteur(_signature: tuple[float, int]) -> LivreRecommender:
    """Cache invalidé quand books.csv change ou quand _MOTEUR_CODE_VERSION est augmenté."""
    _ = _signature
    return LivreRecommender()


def liste_annees_depuis_df(eng: LivreRecommender) -> list[int]:
    """Si une vieille version du module recommender est encore en cache."""
    out: list[int] = []
    for x in eng.df["annee"].dropna().unique():
        try:
            y = int(float(x))
            if y > 0:
                out.append(y)
        except (TypeError, ValueError):
            continue
    return sorted(set(out))


def annee_vers_option(v: str | int | None) -> int | None:
    if v is None or str(v).strip() in ("", "(toutes)"):
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def ajouter_au_panier(book_id: int) -> bool:
    p = st.session_state.panier
    if book_id in p:
        return False
    p.append(book_id)
    return True


def retirer_du_panier(book_id: int) -> None:
    st.session_state.panier = [x for x in st.session_state.panier if x != book_id]


def aller_a_selection(book_id: int) -> None:
    """Ne modifie pas `sidebar_nav` ici : la radio l’interdit après instanciation."""
    st.session_state.livre_id = int(book_id)
    st.session_state._pending_nav = NAV_LABELS[2]
    st.toast("Ouverture de **Ma sélection**…", icon="✨")


def appliquer_navigation_en_attente() -> None:
    """À appeler avant `st.radio(key='sidebar_nav')` sur chaque exécution du script."""
    cible = st.session_state.pop("_pending_nav", None)
    if cible is not None and cible in NAV_LABELS:
        st.session_state.sidebar_nav = cible


def render_accueil(eng: LivreRecommender, df_cat) -> None:
    st.header("Accueil")
    st.caption("Recherchez, filtrez, puis consultez les recommandations ou remplissez votre panier.")

    q = st.text_input(
        "Recherche générale",
        placeholder="Mots du titre, auteur, genre…",
        key="input_q_general",
    )
    c1, c2, c3 = st.columns([1.2, 1.2, 0.9])
    with c1:
        auteur_f = st.text_input(
            "Auteur (contient)",
            placeholder="ex. Austen",
            key="input_auteur",
        )
    with c2:
        genres = ["(tous)"] + eng.genres_distincts()
        genre_f = st.selectbox("Genre", genres, key="select_genre_accueil")
    with c3:
        annees = (
            eng.annees_disponibles()
            if hasattr(eng, "annees_disponibles")
            else liste_annees_depuis_df(eng)
        )
        opts_annee = ["(toutes)"] + [str(y) for y in annees]
        annee_f = st.selectbox("Année", opts_annee, key="select_annee_accueil")

    annee_int = annee_vers_option(annee_f if annee_f != "(toutes)" else None)

    sig = (
        q.strip().lower(),
        genre_f,
        auteur_f.strip().lower(),
        annee_f,
    )
    if st.session_state.get("_sig_accueil") != sig:
        st.session_state._sig_accueil = sig
        st.session_state.catalogue_page = 1

    vue = eng.filtrer(
        q_general=q,
        genre=None if genre_f == "(tous)" else genre_f,
        auteur=auteur_f,
        annee=annee_int,
    )
    ids_vue = [int(i) for i in vue["id"].tolist()]

    if not ids_vue:
        st.warning("Aucun livre ne correspond à ces critères.")
        return

    total_pages = max(1, math.ceil(len(ids_vue) / PAGE_SIZE))
    page = min(max(1, int(st.session_state.catalogue_page)), total_pages)
    st.session_state.catalogue_page = page
    start = (page - 1) * PAGE_SIZE
    ids_page = ids_vue[start : start + PAGE_SIZE]

    st.divider()
    pager = st.columns([1.1, 2.6, 1.1])
    with pager[0]:
        if st.button("« Page précédente", disabled=page <= 1, key="acc_prev"):
            st.session_state.catalogue_page = page - 1
            st.rerun()
    with pager[1]:
        st.markdown(
            f"<div style='text-align:center;padding-top:8px'><strong>{page}/{total_pages}</strong> "
            f"· {len(ids_vue)} livres</div>",
            unsafe_allow_html=True,
        )
    with pager[2]:
        if st.button("Page suivante »", disabled=page >= total_pages, key="acc_next"):
            st.session_state.catalogue_page = page + 1
            st.rerun()

    sel_actif = int(st.session_state.livre_id)
    for r in range(math.ceil(len(ids_page) / COLS_GRID)):
        cols = st.columns(COLS_GRID, gap="small")
        for c in range(COLS_GRID):
            idx = r * COLS_GRID + c
            if idx >= len(ids_page):
                break
            bid = ids_page[idx]
            row = df_cat[df_cat["id"] == bid].iloc[0]
            url = str(row.get("couverture_url") or "").strip()
            titre = str(row["titre"])
            auteur = str(row["auteur"])
            is_sel = bid == sel_actif
            with cols[c]:
                if url:
                    st.image(url, use_container_width=True)
                else:
                    st.caption("Pas d’image")
                if is_sel:
                    st.markdown("<small>⭐ Sélection courante</small>", unsafe_allow_html=True)
                st.caption(f"**#{bid}** · {titre[:40]}{'…' if len(titre) > 40 else ''}")
                st.caption(auteur[:32])
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Voir reco", key=f"reco_{bid}_p{page}", type="primary"):
                        aller_a_selection(bid)
                        st.rerun()
                with b2:
                    if st.button("Au panier", key=f"cart_{bid}_p{page}"):
                        ok = ajouter_au_panier(bid)
                        st.toast("Ajouté au panier !" if ok else "Déjà dans vos bouquins.", icon="🛒")
                        st.rerun()


def render_panier(eng: LivreRecommender, df_cat) -> None:
    st.header("Mes bouquins")
    p = st.session_state.panier
    if not p:
        st.info("Votre panier est vide. Depuis **Accueil**, cliquez sur **Au panier** pour y ajouter des titres.")
        return

    st.caption(f"{len(p)} titre(s)")
    COLS = 4
    for r in range(math.ceil(len(p) / COLS)):
        cols = st.columns(COLS, gap="small")
        for c in range(COLS):
            i = r * COLS + c
            if i >= len(p):
                break
            bid = p[i]
            liv = eng.par_id(bid)
            if liv is None:
                continue
            with cols[c]:
                u = liv.get("couverture_url") or ""
                if u:
                    st.image(u, use_container_width=True)
                st.markdown(f"**{liv['titre'][:50]}**")
                st.caption(liv["auteur"])
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("Reco", key=f"pk_reco_cart_{bid}"):
                        aller_a_selection(bid)
                        st.rerun()
                with bc2:
                    if st.button("Retirer", key=f"pk_rm_cart_{bid}"):
                        retirer_du_panier(bid)
                        st.toast("Retiré du panier", icon="🗑️")
                        st.rerun()


def render_selection(eng: LivreRecommender, df_cat) -> None:
    st.header("Ma sélection")
    lid = int(st.session_state.livre_id)
    courant = eng.par_id(lid)
    if courant is None:
        st.error("Livre inconnu.")
        return

    c1, c2 = st.columns([1.05, 1.35], gap="large")
    with c1:
        st.subheader("Livre choisi")
        u = courant.get("couverture_url") or ""
        if u:
            st.image(u, width=280)
        st.markdown(f"### {courant['titre']}")
        st.write(f"{courant['auteur']} · *{courant['genre']}* · {courant.get('annee', '')}")
        desc = str(courant.get("description") or "").strip()
        if desc:
            st.write(desc[:1400])

        if st.button("Ajouter à mes bouquins", key="add_sel_to_cart", use_container_width=True):
            ok = ajouter_au_panier(lid)
            st.toast("Ajouté !" if ok else "Déjà dans vos bouquins.", icon="🛒")
            st.rerun()

        st.divider()
        st.caption("💡 Choisissez un autre titre depuis **Accueil** puis **Voir reco**, ou depuis **Mes bouquins**.")

    with c2:
        st.subheader("Suggestions similaires (TF–IDF)")
        reco = eng.recommander(lid, k=NB_VOISINS)
        if not reco:
            st.info("Pas assez de voisins textuels pour ce titre.")
        else:
            max_s = max(s for _, s in reco) or 1e-9
            for row_start in range(0, len(reco), 3):
                chunk = reco[row_start : row_start + 3]
                rc = st.columns(len(chunk))
                for col, (liv, score) in zip(rc, chunk):
                    with col:
                        lu = liv.get("couverture_url") or ""
                        if lu:
                            st.image(lu, use_container_width=True)
                        t = liv["titre"]
                        short = t if len(t) < 56 else t[:53] + "…"
                        st.markdown(f"**{short}**")
                        st.caption(liv["auteur"])
                        rel = min(1.0, score / max_s)
                        st.progress(rel, text=f"Pertinence {rel * 100:.0f} %")

                        oid = int(liv["id"])
                        cta1, cta2 = st.columns(2)
                        with cta1:
                            if st.button("Voir", key=f"sreco_{lid}_{oid}"):
                                aller_a_selection(oid)
                                st.rerun()
                        with cta2:
                            if st.button("+", key=f"scart_{lid}_{oid}", help="Au panier"):
                                ok = ajouter_au_panier(oid)
                                st.toast("Ajouté !" if ok else "Déjà présent.", icon="🛒")
                                st.rerun()


inject_animations_css()
try:
    _csv_mtime = _DATA_CSV.stat().st_mtime
except OSError:
    _csv_mtime = 0.0
eng = moteur((_csv_mtime, _MOTEUR_CODE_VERSION))
df_cat = eng.df

try:
    _ = df_cat.iloc[0]
except Exception:
    st.error(
        "Fichier **data/books.csv** introuvable ou vide. "
        "Remettez-le dans `data/` puis rechargez la page."
    )
    st.stop()

if "livre_id" not in st.session_state:
    st.session_state.livre_id = int(df_cat["id"].iloc[0])
if "catalogue_page" not in st.session_state:
    st.session_state.catalogue_page = 1
if "panier" not in st.session_state:
    st.session_state.panier = []
if "sidebar_nav" not in st.session_state:
    st.session_state.sidebar_nav = NAV_LABELS[0]

appliquer_navigation_en_attente()

with st.sidebar:
    st.title("Navigation")
    st.radio(
        "Pages",
        list(NAV_LABELS),
        key="sidebar_nav",
        label_visibility="collapsed",
    )
    n_cart = len(st.session_state.panier)
    st.metric("Mes bouquins", f"{n_cart} titre(s)")
    st.divider()
    st.caption(
        "Recommandation par **contenu** : TF–IDF + cosinus. "
        f"Fixé à **{NB_VOISINS}** suggestions."
    )

page = str(st.session_state.sidebar_nav)

if page == NAV_LABELS[0]:
    render_accueil(eng, df_cat)
elif page == NAV_LABELS[1]:
    render_panier(eng, df_cat)
else:
    render_selection(eng, df_cat)
