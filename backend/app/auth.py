import os

import requests

GITHUB_OAUTH_CLIENT_ID = os.environ.get("GITHUB_OAUTH_CLIENT_ID")
GITHUB_OAUTH_CLIENT_SECRET = os.environ.get("GITHUB_OAUTH_CLIENT_SECRET")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8002")
GITHUB_OAUTH_REDIRECT_URI = f"{BACKEND_URL}/auth/github/callback"


def get_github_login_url(state: str) -> str:
    return (
        "https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_OAUTH_CLIENT_ID}"
        f"&redirect_uri={GITHUB_OAUTH_REDIRECT_URI}"
        f"&state={state}"
    )


def exchange_code_for_token(code: str) -> str:
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_OAUTH_CLIENT_ID,
            "client_secret": GITHUB_OAUTH_CLIENT_SECRET,
            "code": code,
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


def fetch_github_profile(access_token: str) -> dict:
    response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    data = response.json()
    return {"id": data["id"], "login": data["login"], "avatar_url": data["avatar_url"]}
