# Dev Factory - Panel Discord

Ce projet met en place un site web (Flask) avec authentification Discord (OAuth2) et un **panneau de gestion** permettant aux membres de l'équipe (staff) de donner des rôles à un utilisateur via son ID Discord.

## 🔧 Installation

1. Copier l'exemple d'environnement :

```bash
cp backend/.env.example backend/.env
```

2. Remplir `backend/.env` avec vos variables (client OAuth, bot token, guild ID, IDs staff, mapping des rôles).

3. Installer les dépendances :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

4. Lancer le serveur :

```bash
python backend/app.py
```

5. Ouvrir `http://localhost:5000` dans votre navigateur.

## 🔐 Notes importantes

- Le bot Discord doit avoir la permission `Manage Roles` et être positionné au-dessus des rôles qu'il doit attribuer.
- `ADMIN_IDS` correspond aux IDs Discord des personnes autorisées à utiliser le panneau.
- Pour attribuer un rôle, il suffit de renseigner l'ID Discord de l'utilisateur cible.

---

## 🧩 Arborescence

- `backend/app.py` : application Flask
- `backend/templates/` : pages HTML
- `backend/static/` : CSS / JS / assets
