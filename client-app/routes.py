from __future__ import annotations

import secrets

import jwt
from flask import Blueprint, redirect, render_template, request, session, url_for

from auth import build_authorize_url, exchange_code, generate_pkce, get_user_profile, refresh_access_token

bp = Blueprint("app", __name__)


def _logged_in() -> bool:
    return "access_token" in session


@bp.route("/")
def index():
    return render_template("index.html", logged_in=_logged_in())


@bp.route("/login")
def login():
    """Start the Authorization Code + PKCE flow.

    Generates a fresh state token (CSRF protection) and PKCE pair, stores
    them in the session, then redirects the user to the auth server.
    """
    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    session["code_verifier"] = code_verifier
    return redirect(build_authorize_url(state, code_challenge))


@bp.route("/callback")
def callback():
    """Handle the redirect back from the auth server.

    Validates state (CSRF check), exchanges the one-time code for tokens,
    and stores them in the server-side session.
    """
    error = request.args.get("error")
    if error:
        desc = request.args.get("error_description", "")
        return render_template("index.html", logged_in=False, error=f"{error}: {desc}")

    returned_state = request.args.get("state", "")
    expected_state = session.pop("oauth_state", None)
    if not expected_state or returned_state != expected_state:
        return render_template("index.html", logged_in=False, error="State mismatch — possible CSRF attack. Please try again.")

    code = request.args.get("code")
    code_verifier = session.pop("code_verifier", None)
    if not code or not code_verifier:
        return render_template("index.html", logged_in=False, error="Missing code or verifier. Please try again.")

    try:
        tokens = exchange_code(code, code_verifier)
    except Exception as exc:
        return render_template("index.html", logged_in=False, error=f"Token exchange failed: {exc}")

    session["access_token"] = tokens["access_token"]
    session["refresh_token"] = tokens.get("refresh_token")
    session["scope"] = tokens.get("scope", "")
    return redirect(url_for("app.profile"))


@bp.route("/profile")
def profile():
    """Show the logged-in user's profile and decoded token claims.

    Educational focus: renders the raw JWT claims so learners can see exactly
    what's in the token (sub, token_type, scope, exp).
    """
    if not _logged_in():
        return redirect(url_for("app.login"))

    access_token = session["access_token"]
    claims = jwt.decode(access_token, options={"verify_signature": False})

    try:
        user_data = get_user_profile(access_token)
        resource_error = None
    except Exception as exc:
        user_data = None
        resource_error = str(exc)

    return render_template(
        "profile.html",
        claims=claims,
        user_data=user_data,
        resource_error=resource_error,
        scope=session.get("scope", ""),
        has_refresh=bool(session.get("refresh_token")),
    )


@bp.route("/refresh")
def refresh():
    """Refresh the access token using the stored refresh token (RFC 6749 §6)."""
    if not _logged_in():
        return redirect(url_for("app.login"))

    rt = session.get("refresh_token")
    if not rt:
        return redirect(url_for("app.profile"))

    try:
        tokens = refresh_access_token(rt)
        session["access_token"] = tokens["access_token"]
    except Exception as exc:
        session.clear()
        return render_template("index.html", logged_in=False, error=f"Token refresh failed: {exc}. Please log in again.")

    return redirect(url_for("app.profile"))


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("app.index"))


@bp.route("/health")
def health():
    return {"status": "ok"}
