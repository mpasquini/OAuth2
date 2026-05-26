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

- [ ] **8. `client-app/` — Flask browser app (Authorization Code flow demo)**
  - `auth.py`: PKCE generation, state param, `/authorize` redirect, `/callback` code exchange, token refresh
  - `routes.py`: `/`, `/callback`, `/profile`, `/logout`
  - `templates/`: login page, profile page
  - `config.py`, `main.py`, `requirements.txt`
  - This is the user-facing counterpart to `scripts/service_client.py`

- [ ] **9. `tests/e2e/` — end-to-end tests (require `make up`)**
  - `test_client_credentials_flow.py`: POST /token → GET /api/service/stats → assert 200 and correct body
  - `test_auth_code_flow.py`: simulate full browser flow programmatically
  - Stub files already created; needs real implementation once services are running
