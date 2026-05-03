# Bibliothèque personnelle — recommandation de livres (démo académique)

Objectif : illustrer une **recommandation par contenu** (TF–IDF + cosinus) avec une **interface Streamlit** conviviale : catalogue paginé, filtres, panier et page dédiée aux suggestions. **Aucun serveur Flask** : tout s’exécute dans Streamlit + un fichier CSV.

---

## Prérequis

- **Python 3.10+**
- **`data/books.csv`** doit être présent (**~200 livres** : métadonnées + URL de couverture Open Library). À **conserver dans le dépôt** si vous poussez sur GitHub.
- Une **connexion Internet** n’est pas nécessaire au calcul des recommandations ; elle sert seulement au navigateur pour **afficher** les images hébergées chez Open Library.

---

## Installation

À la racine du projet :

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### Dépendances (`requirements.txt`)

| Paquet        | Usage principal        |
|---------------|-------------------------|
| `streamlit`   | Interface utilisateur   |
| `pandas`      | Lecture du CSV          |
| `scikit-learn`| TF–IDF, similarité cosinus |

---

## Lancer l’application

```bash
streamlit run streamlit_app.py
```

---

## Utilisation de l’interface

La **barre latérale** propose trois vues (radio **Navigation**) :

### Accueil

- En haut : **recherche générale** (recherche dans titre, auteur, genre, description si présente).
- **Filtres** : auteur (texte « contient »), **genre**, **année** (liste dérivée du CSV).
- **Pagination** : **20 livres par page**, boutons « Page précédente / suivante ».
- Pour chaque carte :
  - **Voir reco** → définit le livre actif et ouvre **Ma sélection** ;
  - **Au panier** → ajoute le titre à **Mes bouquins** (sans doublon).

### Mes bouquins

- Liste des livres ajoutés au **panier** (identifiants en session ; la liste est réinitialisée si vous fermez l’onglet / la session).
- **Reco** sur une ligne → ouvre **Ma sélection** pour ce livre.
- **Retirer** enlève le titre du panier.

### Ma sélection

- Affiche le **livre choisi** (couverture, métadonnées) et **8 suggestions** similaires (**nombre fixe**, non modifiable dans l’UI).
- Possibilité d’**ajouter** le livre courant au panier ou d’ouvrir une suggestion (**Voir** → nouvelle sélection + rechargement des recommandations).

### Effets visuels

Une feuille de style injectée dans l’app applique de **légères animations** (fondu à l’entrée de la page principale, léger zoom au survol des couvertures, transitions sur les boutons).

---

## Comment ça marche ? (algorithme)

1. Chaque livre est représenté par un **texte concaténé** (titre + auteur + genre + description).
2. **TF–IDF** transforme ces textes en vecteurs creux.
3. La **similarité cosinus** entre le livre sélectionné et les autres produit un classement ; on garde les **8 meilleurs** (`NB_VOISINS` dans `streamlit_app.py`).

**Limite pédagogique** : pas de filtrage collaboratif (pas de profils utilisateurs ni de matrices de notes utilisateur × livre). Les suggestions sont uniquement « proches du texte » du livre courant.

---

## Fichiers du projet

| Fichier / dossier | Rôle |
|-------------------|------|
| `data/books.csv` | Catalogue (~200 lignes + couvertures) |
| `recommender.py` | Classe `LivreRecommender` : lecture CSV, `filtrer`, `annees_disponibles`, `genres_distincts`, `recommander` |
| `streamlit_app.py` | Navigation, filtres, panier, pagination, reco, CSS animations |
| `requirements.txt` | Dépendances Python |
| `.gitignore` | Fichiers locaux à ne pas pousser (ex. `.venv`) |

---

## Cache Streamlit (`@st.cache_resource`)

Le chargeur CSV / modèle TF–IDF est mis en cache avec une signature **`(date de modification de books.csv, version code)`**. Si vous modifiez `recommender.py` et voyez des incohérences, **incrémentez `_MOTEUR_CODE_VERSION`** dans `streamlit_app.py` ou utilisez le menu Streamlit : **⚙️ Caches → Clear cached resource**.

---

## GitHub — avant un `push`

- Inclure **`data/books.csv`** si vous voulez que le projet soit cloné et fonctionnel tout de suite.
- Ne **pas** commiter `.venv/` (normalement ignoré via `.gitignore`).
- Une fois poussé, les instructions **Installation** + **Lancer l’application** suffisent à reproduire l’environnement.

---
