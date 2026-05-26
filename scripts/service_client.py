#!/usr/bin/env python3
"""Client Credentials Flow demo.

Demonstrates the full machine-to-machine OAuth2 flow in one script:

  1. POST /token with client_id + client_secret (no browser, no user)
  2. Print the decoded token claims — note sub = client_id, not a user ID
  3. Call GET /api/service/stats with the token
  4. Print the response

Run with:
    python scripts/service_client.py
    make demo-cc
"""

import base64
import json
import sys
import urllib.request
import urllib.parse
import urllib.error

# ---------------------------------------------------------------------------
# Configuration — mirrors .env.example SERVICE_CLIENT_* variables
# ---------------------------------------------------------------------------

AUTH_SERVER   = "http://localhost:5000"
RESOURCE_SERVER = "http://localhost:5002"
CLIENT_ID     = "service-client"
CLIENT_SECRET = "service-client-secret"
SCOPE         = "read:stats"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def post_form(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_json(url: str, token: str) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def decode_jwt_payload(token: str) -> dict:
    """Decode JWT claims without verifying signature (demo only)."""
    payload_b64 = token.split(".")[1]
    # Pad to a multiple of 4 for base64 decoding
    payload_b64 += "=" * (-len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))


def section(title: str):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print('─' * 50)


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def main():
    # ------------------------------------------------------------------
    # Step 1 — Request a token from the Authorization Server
    # ------------------------------------------------------------------
    section("Step 1 — Request token (Client Credentials)")
    print(f"  POST {AUTH_SERVER}/token")
    print(f"  grant_type=client_credentials")
    print(f"  client_id={CLIENT_ID!r}  scope={SCOPE!r}")

    try:
        token_response = post_form(f"{AUTH_SERVER}/token", {
            "grant_type":    "client_credentials",
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope":         SCOPE,
        })
    except urllib.error.HTTPError as e:
        print(f"\n  ERROR {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\n  Cannot reach auth server at {AUTH_SERVER}: {e.reason}", file=sys.stderr)
        print("  Is 'make up' running?", file=sys.stderr)
        sys.exit(1)

    access_token = token_response["access_token"]
    print(f"\n  token_type : {token_response['token_type']}")
    print(f"  expires_in : {token_response['expires_in']}s")
    print(f"  scope      : {token_response['scope']}")
    # Confirm no refresh token — key difference from Authorization Code flow
    print(f"  refresh_token: {'present' if 'refresh_token' in token_response else 'NOT present (expected for client credentials)'}")

    # ------------------------------------------------------------------
    # Step 2 — Decode and inspect the token claims
    # ------------------------------------------------------------------
    section("Step 2 — Token claims (decoded, no signature check)")
    claims = decode_jwt_payload(access_token)
    for key, value in claims.items():
        print(f"  {key:12} : {value}")
    print()
    print("  ↑ sub is the client_id — no user is involved in this flow")

    # ------------------------------------------------------------------
    # Step 3 — Call the machine API on the Resource Server
    # ------------------------------------------------------------------
    section("Step 3 — Call Resource Server machine API")
    print(f"  GET {RESOURCE_SERVER}/api/service/stats")

    try:
        stats = get_json(f"{RESOURCE_SERVER}/api/service/stats", access_token)
    except urllib.error.HTTPError as e:
        print(f"\n  ERROR {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\n  Cannot reach resource server at {RESOURCE_SERVER}: {e.reason}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 4 — Print the response
    # ------------------------------------------------------------------
    section("Step 4 — Response")
    print(json.dumps(stats, indent=2))
    print()
    print("  Client Credentials flow complete.")
    print("  Compare with the Authorization Code flow: no browser, no user,")
    print("  no consent screen — just credentials in, token out.")


if __name__ == "__main__":
    main()
