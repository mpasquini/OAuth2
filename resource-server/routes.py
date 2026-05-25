from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from security import require_client_token, require_oauth2

router = APIRouter()


# ---------------------------------------------------------------------------
# User endpoints — Authorization Code flow tokens only
# ---------------------------------------------------------------------------

@router.get("/api/user/profile")
def get_user_profile(request: Request, _=Depends(require_oauth2)):
    """Return the authenticated user's profile.
    Token must have token_type='user' (issued via Authorization Code flow).
    """
    user = request.state.oauth2_user
    return {
        "sub": user["sub"],
        "scope": user.get("scope", ""),
        "token_type": user["token_type"],
    }


@router.get("/api/user/data")
def get_user_data(request: Request, _=Depends(require_oauth2)):
    """Return protected data scoped to the authenticated user."""
    user = request.state.oauth2_user
    return {
        "user_id": user["sub"],
        "data": [
            {"id": 1, "title": "Item one", "value": 42},
            {"id": 2, "title": "Item two", "value": 17},
        ],
    }


# ---------------------------------------------------------------------------
# Machine endpoint — Client Credentials flow tokens only
# ---------------------------------------------------------------------------

@router.get("/api/service/stats")
def get_service_stats(request: Request, _=Depends(require_client_token)):
    """Aggregate stats endpoint for machine clients.

    No user context — the caller is a service, not a human.
    Token must have token_type='client' (issued via Client Credentials flow).

    This is the concrete difference learners should observe:
      - User token  → /api/user/*   (sub = user ID, has a person behind it)
      - Client token → /api/service/* (sub = client_id, no user involved)
    """
    client = request.state.oauth2_client
    return {
        "requested_by": client["sub"],      # client_id, e.g. "service-client"
        "scope": client.get("scope", ""),
        "stats": {
            "total_users": 3,
            "active_tokens": 12,
            "requests_today": 847,
        },
    }


# ---------------------------------------------------------------------------
# Health check — no auth required
# ---------------------------------------------------------------------------

@router.get("/health")
def health():
    return {"status": "ok"}
