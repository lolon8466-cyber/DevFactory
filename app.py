"""Dev Factory - Panel d'administration Discord

Usage:
  - Configurez les variables d'environnement (voir backend/.env.example)
  - Installez les dépendances: pip install -r backend/requirements.txt
  - Lancez: python backend/app.py

Le site permet de se connecter via Discord (OAuth2) et, si l'utilisateur est dans la liste du staff,
de gérer l'attribution de rôles dans le serveur Discord (via un bot).
"""

import os
from urllib.parse import urlencode

import requests
from flask import Flask, flash, redirect, render_template, request, session, url_for
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET", "change-me")

# ==================== Configuration ====================
DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "8486631cbb549606f11f5a5c4e13ff04943a9493e253fde306a33df6db12f1dd")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "k-mXll56jtQCukVPyUmKjZr2Tv_H4OvU")
DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI", "http://localhost:5000/callback")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "MTQ3ODc5MDY3NjI1MzYzODc3Mg.GpCnBr.n0K64A0StM6_Nwl6mLGYgTt2SxhhFH-6El83u8")

# Extracted from "https://discord.com/channels/1312543189856551042/1483889230043152516"
DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID", "1312543189856551042")

# Liste des IDs Discord (Administrateurs / Staff) qui peuvent accéder au panneau de gestion.
ADMIN_IDS = [s.strip() for s in (os.environ.get("ADMIN_IDS", "1296503985443835947,1398425974227337330")).split(",") if s.strip()]

# Exemple de rôle à attribuer avec le formulaire. Vous pouvez définir plusieurs rôles (voir frontend).
ROLE_MAPPING = {
    part.split(":")[0]: part.split(":")[1]
    for part in (os.environ.get("ROLE_MAPPING", "Support:1469975483352355000,Staff:1469975485550166154")).split(",")
    if ":" in part
}

OAUTH_AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"
OAUTH_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API_BASE = "https://discord.com/api"

SCOPES = ["identify", "email"]

# ==================== Helpers ====================

def is_logged_in() -> bool:
    return "user" in session


def is_admin() -> bool:
    user = session.get("user")
    if not user:
        return False
    return str(user.get("id")) in ADMIN_IDS


def get_discord_authorize_url() -> str:
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
    }
    return f"{OAUTH_AUTHORIZE_URL}?{urlencode(params)}"


def discord_api_request(method: str, endpoint: str, **kwargs):
    url = f"{DISCORD_API_BASE}{endpoint}"
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bot {DISCORD_BOT_TOKEN}"
    headers.setdefault("Content-Type", "application/json")
    return requests.request(method, url, headers=headers, **kwargs)

# ==================== Routes ====================

@app.route("/")
def home():
    return render_template(
        "index.html",
        logged_in=is_logged_in(),
        user=session.get("user"),
        admin=is_admin(),
        role_mapping=ROLE_MAPPING,
        DISCORD_CLIENT_ID=DISCORD_CLIENT_ID,
    )


@app.route("/login")
def login():
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
        flash(
            "Les variables d'environnement DISCORD_CLIENT_ID / DISCORD_CLIENT_SECRET ne sont pas configurées.",
            "danger",
        )
        return redirect(url_for("home"))

    return redirect(get_discord_authorize_url())


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        flash("Aucun code OAuth reçu.", "danger")
        return redirect(url_for("home"))

    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "scope": " ".join(SCOPES),
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_response = requests.post(OAUTH_TOKEN_URL, data=data, headers=headers)
    token_response.raise_for_status()
    token_data = token_response.json()

    access_token = token_data.get("access_token")

    user_resp = requests.get(
        f"{DISCORD_API_BASE}/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    user_resp.raise_for_status()
    user = user_resp.json()

    session["user"] = user
    session["access_token"] = access_token

    return redirect(url_for("home"))


@app.route("/assign-role", methods=["POST"])
def assign_role():
    if not is_logged_in() or not is_admin():
        flash("Accès refusé : vous n'avez pas les droits nécessaires.", "danger")
        return redirect(url_for("home"))

    target_id = request.form.get("target_id")
    role_id = request.form.get("role_id")

    if not target_id or not role_id:
        flash("Veuillez fournir un ID/utilisateur et sélectionner un rôle.", "warning")
        return redirect(url_for("home"))

    # Si on a un pseudo#1234, tenter de récupérer l'ID via l'API Guild members.
    if "#" in target_id:
        parts = target_id.split("#", 1)
        if len(parts) != 2:
            flash(
                'Format invalide. Utilisez "pseudo#1234" ou un ID utilisateur.', "warning"
            )
            return redirect(url_for("home"))

        username, discriminator = parts
        response = discord_api_request(
            "GET",
            f"/guilds/{DISCORD_GUILD_ID}/members/search",
            params={"query": username, "limit": 10},
        )

        if response.status_code != 200:
            flash(
                "Impossible de rechercher l'utilisateur dans le serveur (permissions manquantes).",
                "danger",
            )
            return redirect(url_for("home"))

        candidates = response.json()
        match = next(
            (m for m in candidates if m.get("user", {}).get("discriminator") == discriminator),
            None,
        )

        if not match:
            flash(
                "Aucun membre trouvé avec ce pseudo#discrim dans le serveur.", "warning"
            )
            return redirect(url_for("home"))

        target_id = match["user"]["id"]

    # Appliquer le rôle via l'API Discord (Ajout d'un rôle sans écraser les autres)
    endpoint = f"/guilds/{DISCORD_GUILD_ID}/members/{target_id}/roles/{role_id}"
    response = discord_api_request("PUT", endpoint)

    if response.status_code in (200, 204):
        flash("Rôle attribué avec succès !", "success")
    else:
        flash(
            f"Erreur {response.status_code} : {response.text[:200]}", "danger"
        )

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
