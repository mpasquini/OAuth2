# Client Credentials Flow - Implementation Plan

Steps to add Client Credentials Flow alongside the existing Authorization Code Flow.
Docs (README.md + AGENTS.md) are already updated. Work through these in order — each builds on the previous.

---

- [x] **1. `auth-server/models.py` — extend `OAuthClient`**
  - Add `allowed_grant_types: list` field (e.g. `["authorization_code"]` or `["client_credentials"]`)
  - Add `allowed_scopes: list` field for per-client scope restriction
  - Update Alembic migration to add both columns

- [x] **2. `auth-server/routes.py` + `security.py` — Client Credentials token issuance**
  - Add `create_client_token(client_id, scopes)` in `security.py` (JWT with `sub=client_id`, no user, no refresh token)
  - Add `grant_type=client_credentials` branch in the `/token` endpoint in `routes.py`:
    - Validate `client_id` + `client_secret` against DB
    - Check `client_credentials` is in `OAuthClient.allowed_grant_types`
    - Issue access token via `create_client_token()`; return no `refresh_token`

- [x] **3. `resource-server/security.py` — add `@require_client_token` decorator**
  - Extract shared JWT validation logic into a helper used by both decorators
  - `@require_oauth2` — existing behaviour, asserts token `sub` is a user ID, populates `request.oauth2_user`
  - `@require_client_token` — new, asserts token `sub` is a client ID, populates `request.oauth2_client`

- [x] **4. `resource-server/routes.py` — add machine API endpoint**
  - Add `GET /api/service/stats` protected with `@require_client_token`
  - Returns aggregate data that makes sense for a background service (no user context)
  - Add tests in `tests/resource_server/test_service_endpoints.py`

- [x] **5. `scripts/service_client.py` — Client Credentials flow demo**
  - ~40-line standalone script (no web server, no Flask)
  - Step 1: POST `/token` with `grant_type=client_credentials`, `client_id`, `client_secret`, `scope`
  - Step 2: Decode and print the token claims (show `sub` = client ID, no `user_id`)
  - Step 3: Call `GET /api/service/stats` with the token
  - Step 4: Print the response
  - Add `demo-cc` and `test-e2e-cc` targets to `Makefile`

- [x] **6. `scripts/seed.py` + `.env.example` — register the service client**
  - Add `service-client` to the clients seeded in `seed.py`:
    - `client_id=service-client`, `client_secret=service-client-secret`
    - `allowed_grant_types=["client_credentials"]`, `allowed_scopes=["read:stats"]`
  - Also seed `web-client` (authorization_code) and test users (alice, bob, charlie)
  - Add `SERVICE_CLIENT_ID`, `SERVICE_CLIENT_SECRET`, `SERVICE_CLIENT_SCOPES` to `.env.example`

- [x] **7. `tests/auth_server/test_token_endpoint.py` — auth server unit tests**
  - Test `grant_type=client_credentials`: token returned, no `refresh_token` in response
  - Test `grant_type=authorization_code`: PKCE verification, one-time code use
  - Test invalid client credentials → 401
  - Test wrong grant type for client → 403
  - Stub file already created; needs real implementation

- [x] **8. `client-app/` — Flask browser app (Authorization Code flow demo)**
  - `auth.py`: PKCE generation, state param, `/authorize` redirect, `/callback` code exchange, token refresh
  - `routes.py`: `/`, `/callback`, `/profile`, `/logout`
  - `templates/`: login page, profile page
  - `config.py`, `main.py`, `requirements.txt`
  - This is the user-facing counterpart to `scripts/service_client.py`

- [x] **9. `tests/e2e/` — end-to-end tests (require `make up`)**
  - `test_client_credentials_flow.py`: POST /token → GET /api/service/stats → assert 200 and correct body
  - `test_auth_code_flow.py`: simulate full browser flow programmatically
  - Stub files already created; needs real implementation once services are running

---

## Docker

`docker-compose.yml` already references all three Dockerfiles. Work through these in order.

- [x] **10. Shared `.dockerignore` (root-level)**
  - Prevents large directories from being sent as build context:
    ```
    graphify-out/
    __pycache__/
    *.pyc
    *.db
    .env
    .git/
    tests/
    htmlcov/
    .pytest_cache/
    ```

- [x] **11. `auth-server/Dockerfile` + `auth-server/entrypoint.sh`**
  - Base image: `python:3.12-slim` (stable; avoids bleeding-edge 3.14 compat issues)
  - Install system deps needed by `bcrypt` C extension: `gcc libffi-dev`
  - Copy `requirements.txt` first (layer-cache pip install before copying source)
  - `WORKDIR /app`, copy source, create non-root user (`appuser`) and `chown`
  - `entrypoint.sh` runs before uvicorn:
    1. `alembic upgrade head` — applies all pending migrations
    2. `python scripts/seed.py` — idempotent; safe to run on every start
    3. `exec uvicorn main:app --host 0.0.0.0 --port ${AUTH_SERVER_PORT:-5000}`
  - `CMD ["/app/entrypoint.sh"]`

- [x] **12. `resource-server/Dockerfile`**
  - Base image: `python:3.12-slim`
  - No DB migrations or seed needed — stateless service
  - Pattern: copy `requirements.txt` → pip install → copy source → non-root user
  - `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5002"]`
  - Port read from `RESOURCE_SERVER_PORT` env var; override in compose if needed

- [ ] **13. `client-app/Dockerfile`**
  - Base image: `python:3.12-slim`
  - Flask is pure Python — no C extensions, no extra system packages needed
  - Pattern: copy `requirements.txt` → pip install → copy source → non-root user
  - `CMD ["python", "main.py"]` (Flask dev server; swap for gunicorn in production)
  - `EXPOSE 5001`

- [ ] **14. `docker-compose.dev.yml` — hot-reload override**
  - Referenced by `make dev` (`docker-compose -f docker-compose.yml -f docker-compose.dev.yml up`)
  - Override each service to mount source and enable reload:
    ```yaml
    services:
      auth-server:
        command: uvicorn main:app --host 0.0.0.0 --port 5000 --reload
        volumes: [./auth-server:/app]
      resource-server:
        command: uvicorn main:app --host 0.0.0.0 --port 5002 --reload
        volumes: [./resource-server:/app]
      client-app:
        command: python main.py          # Flask debug=True handles reload
        environment:
          FLASK_ENV: development
        volumes: [./client-app:/app]
    ```
  - Source volume mounts already exist in `docker-compose.yml` for all three services,
    so the only additions here are the `--reload` commands and `FLASK_ENV`

---

## RFC 9700 Security Review

Audit against [OAuth 2.0 Security Best Current Practice (RFC 9700)](https://datatracker.ietf.org/doc/html/rfc9700).
Each finding lists the RFC section, severity, exact file:line, and the fix required.

### Bugs (broken at runtime)

- [x] **Refresh token never persisted** — `auth-server/routes.py:305`
  - `generate_code()` produces a refresh token and returns it in the response, but it is never
    written to the database. The `/refresh` endpoint at `routes.py:336` queries
    `Token.access_token == refresh_token`, which will never match — `/refresh` is effectively broken.
  - **Fix**: add a `refresh_token` column to `Token` (or a separate `RefreshToken` model), write the
    token on issuance, query by that column in `/refresh`, and mark it used/expired after rotation.

### MUST violations (RFC 9700)

- [ ] **PKCE downgrade attack not blocked** — `auth-server/routes.py:293` — §2.1.1
  - Current guard: `if auth_code.code_challenge:` — when no challenge was stored (code issued without
    PKCE), a `code_verifier` in the token request is silently ignored instead of rejected.
  - RFC 9700 §2.1.1: *"if there was no code_challenge in the authorization request, a request to the
    token endpoint containing a code_verifier MUST be rejected."*
  - **Fix**:
    ```python
    if auth_code.code_challenge:
        # existing PKCE check
    elif code_verifier:
        _oauth2_error("invalid_request", "code_verifier sent but no code_challenge was used")
    ```

- [ ] **HTTP redirect URIs not rejected for non-localhost clients** — `auth-server/routes.py:119` — §4.1.3
  - The server validates that `redirect_uri` is in the registered list but does not enforce HTTPS.
  - RFC 9700 §4.1.3: *"Authorization servers MUST NOT allow redirect URIs that use the http scheme
    except for native clients that use loopback interface redirection."*
  - **Fix**: in `authorize_get`, after the redirect_uri check, reject any `http://` URI whose host is
    not `127.0.0.1`, `::1`, or `localhost`.

### SHOULD violations (RFC 9700)

- [ ] **Redirect uses 302 instead of 303** — `auth-server/routes.py:146,174` — §4.11
  - Both success and error redirects from `/authorize` use `status_code=302`. HTTP 302 allows the
    browser to forward the original method (POST), potentially re-submitting credentials.
  - RFC 9700 §4.11: *"Authorization servers SHOULD use HTTP 303 (See Other) instead of 307."*
    303 unconditionally switches to GET, preventing credential forwarding.
  - **Fix**: change both `RedirectResponse(..., status_code=302)` calls to `status_code=303`.

- [ ] **No audience (`aud`) claim in tokens** — `auth-server/security.py:30` — §2.3
  - `_build_payload()` emits `sub`, `token_type`, `scope`, `iat`, `exp` — no `aud`.
  - RFC 9700 §2.3: *"Access tokens SHOULD be audience-restricted to a specific resource server."*
    Without `aud`, a token issued for the resource server is equally valid against any other service
    that shares the same secret key.
  - **Fix**: add `"aud": resource_server_url` to `_build_payload`; add audience validation in
    `resource-server/security.py:_decode_jwt()` using `jwt.decode(..., audience=EXPECTED_AUD)`.

- [ ] **Access tokens stored as plaintext** — `auth-server/models.py:Token.access_token` — §2.3
  - The `Token` table stores the raw JWT string. If the database is compromised, all issued tokens
    are immediately usable.
  - RFC 9700 §2.3: *"Authorization servers MUST treat access tokens like other sensitive secrets and
    not store or transfer them in plaintext."*
  - **Fix**: store `sha256(access_token)` in the DB (hex digest); compare hash on lookup and
    introspection. The raw token leaves the server only in the HTTP response.

- [ ] **No refresh token rotation** — `auth-server/routes.py:320` — §4.13.2
  - The `/refresh` endpoint returns a new access token but reuses the same refresh token forever
    (until expiry). Replay of a stolen refresh token is undetectable.
  - RFC 9700 §4.13.2: *"Refresh tokens for public clients MUST be sender-constrained or use refresh
    token rotation."* For confidential clients (like `web-client`) rotation is RECOMMENDED.
  - **Fix**: on each `/refresh` call, invalidate the presented refresh token (set `revoked=True`) and
    issue a new one; return both in the response.

### Out of scope for this educational project

The following RFC 9700 recommendations require infrastructure beyond a local dev stack and are
intentionally not implemented. They are documented here so learners know what a production deployment
would add:

| Recommendation | RFC 9700 ref | Production approach |
|---|---|---|
| Sender-constrained tokens (mTLS / DPoP) | §2.2.1 | OAuth 2.0 DPoP (RFC 9449) or mutual TLS (RFC 8705) |
| Asymmetric client authentication | §5.2.2 | `private_key_jwt` (RFC 7523) instead of `client_secret` |
| TLS enforcement end-to-end | §1.2 | Terminate TLS at a reverse proxy (nginx/caddy); enforce HTTPS-only redirect URIs in production |
| Refresh token inactivity expiry | §4.13.2 | Track `last_used_at`; reject tokens idle > N days |
