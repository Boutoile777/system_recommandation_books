# Bibliothèque personnelle — recommandation de livres (démo académique)

Objectif : illustrer une **recommandation par contenu** (TF–IDF + cosinus) avec une **interface Streamlit** : catalogue paginé, filtres, panier et page dédiée aux suggestions. **Aucun serveur Flask** : tout tourne avec Streamlit et un fichier CSV.

---

## Prérequis

- **Python 3.10+**
- Fichier **`data/books.csv`** avec **environ 200 lignes** (colonnes : id, titre, auteur, genre, année, description, url de couverture).  
  Ce fichier peut être **fourni dans le dépôt** ou **régénéré** (voir ci‑dessous).
- **Affichage des couvertures** : chaques URL pointe vers **Open Library** ; le navigateur charge les images **si une connexion Internet est disponible** au moment où vous utilisez l’application.

---

## Installation (nouveau dossier ou clone GitHub)

Ouvrez un terminal dans le dossier racine du projet (`Recommandation_système`) puis :

### 1. Créer et activer un environnement virtuel

```bash
python -m venv .venv
```

**Windows (PowerShell ou CMD)**

```bash
.\.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 2. Installer les bibliothèques Python

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. (Re)créer le catalogue **`data/books.csv`**

À faire **si le CSV est vide, manquant, ou après un problème Git** (pour éviter l’erreur *empty vocabulary* du TF-IDF).

- **Connexion Internet obligatoire** pour cet étape.
- Le script télécharge environ **200 livres** depuis l’API **Open Library**, avec **une couverture par livre**, en **répartissant les entrées entre plusieurs genres / sujets**.

```bash
python scripts/fetch_books_ol.py
```

Vous devez voir un message du type : `200 livres écrits dans ...\data\books.csv`.

Ensuite :

```bash
streamlit run streamlit_app.py
```

### Dépendances (`requirements.txt`)

| Paquet           | Usage principal                           |
|------------------|-------------------------------------------|
| `streamlit`      | Interface utilisateur                     |
| `pandas`         | Lecture du CSV                            |
| `scikit-learn`   | TF–IDF et similarité cosinus              |
| `requests`       | Script optionnel `fetch_books_ol.py`       |

---

## Lancer l’application (installation déjà faite)

```bash
# activez toujours le venv si besoin :
# .\.venv\Scripts\activate   (Windows)
# source .venv/bin/activate  (macOS / Linux)

streamlit run streamlit_app.py
```

---

## Erreurs fréquentes

| Message / situation | Cause probable | Action |
|---------------------|----------------|--------|
| `empty vocabulary` / `ValueError` au chargement | `books.csv` sans données (en-tête seul) | Exécutez `python scripts/fetch_books_ol.py` |
| Message explicite sur fichier vide (`recommender.py`) | Même chose | Idem |
| `RemoteDisconnected` / `ConnectionError` pendant le script | Open Library ferme parfois la connexion (charge, réseau) | Réessayez quelques minutes après ; le script retente automatiquement et **ralentit** entre chaque page — un second lancement suffit souvent |

Après avoir remplacé `books.csv`, si Streamlit gardait une vieille version en cache : menu **⚙️ → Clear cached resource**, ou augmentez **`_MOTEUR_CODE_VERSION`** dans `streamlit_app.py`.

---

## Utilisation de l’interface

La **barre latérale** propose trois vues (**Navigation**) :

### Accueil

- **Recherche générale**, filtres **auteur**, **genre**, **année**.
- Pagination **20 livres / page**.
- **Voir reco** → ouvre **Ma sélection** ; **Au panier** ajoute aux **Mes bouquins**.

### Mes bouquins

- Panier (session navigateur).
- **Reco** / **Retirer**.

### Ma sélection

- Livre actif et **8 suggestions** (nombre fixe, `NB_VOISINS`).

### Animations

Léger fondu à l’ouverture, zoom léger au survol des couvertures, transitions sur les boutons dans la zone principale.

---

## Comment ça marche ? (algorithme)

1. Texte concaténé par livre : titre, auteur, genre, description.
2. **TF–IDF** → vecteurs.
3. **Similarité cosinus** → liste des voisins (**8** retenus par défaut).

Pas de **filtrage collaboratif** (pas de préférences utilisateur ni de grades collectifs dans ce prototype).

---

## Fichiers du projet

| Fichier / dossier | Rôle |
|-------------------|------|
| `data/books.csv` | Catalogue + URLs de couvertures |
| `scripts/fetch_books_ol.py` | Régénérer ~200 livres variés depuis Open Library |
| `recommender.py` | `LivreRecommender` : lecture CSV, filtres, recommandations |
| `streamlit_app.py` | Application Streamlit complète |
| `requirements.txt` | Dépendances |
| `.gitignore` | Exclusion de `.venv`, etc. |

---

## GitHub — avant un `push`

- Inclure **`data/books.csv`** si vous voulez un projet **fonctionnel sans relancer le script** après clone.
- Ne **pas** versionner `.venv/`.
- Indiquez dans le README / rapport que **`fetch_books_ol.py`** permet de **réparer** ou **réinitialiser** le jeu de données.

---
