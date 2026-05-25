# Client Credentials Flow - Implementation Plan

Steps to add Client Credentials Flow alongside the existing Authorization Code Flow.
Docs (README.md + AGENTS.md) are already updated. Work through these in order — each builds on the previous.

---

- [x] **1. `auth-server/models.py` — extend `OAuthClient`**
  - Add `allowed_grant_types: list` field (e.g. `["authorization_code"]` or `["client_credentials"]`)
  - Add `allowed_scopes: list` field for per-client scope restriction
  - Update Alembic migration to add both columns

- [ ] **2. `auth-server/routes.py` + `security.py` — Client Credentials token issuance**
  - Add `create_client_token(client_id, scopes)` in `security.py` (JWT with `sub=client_id`, no user, no refresh token)
  - Add `grant_type=client_credentials` branch in the `/token` endpoint in `routes.py`:
    - Validate `client_id` + `client_secret` against DB
    - Check `client_credentials` is in `OAuthClient.allowed_grant_types`
    - Issue access token via `create_client_token()`; return no `refresh_token`

- [ ] **3. `resource-server/security.py` — add `@require_client_token` decorator**
  - Extract shared JWT validation logic into a helper used by both decorators
  - `@require_oauth2` — existing behaviour, asserts token `sub` is a user ID, populates `request.oauth2_user`
  - `@require_client_token` — new, asserts token `sub` is a client ID, populates `request.oauth2_client`

- [ ] **4. `resource-server/routes.py` — add machine API endpoint**
  - Add `GET /api/service/stats` protected with `@require_client_token`
  - Returns aggregate data that makes sense for a background service (no user context)
  - Add tests in `tests/resource_server/test_service_endpoints.py`

- [ ] **5. `scripts/service_client.py` — Client Credentials flow demo**
  - ~40-line standalone script (no web server, no Flask)
  - Step 1: POST `/token` with `grant_type=client_credentials`, `client_id`, `client_secret`, `scope`
  - Step 2: Decode and print the token claims (show `sub` = client ID, no `user_id`)
  - Step 3: Call `GET /api/service/stats` with the token
  - Step 4: Print the response
  - Add `demo-cc` and `test-e2e-cc` targets to `Makefile`

- [ ] **6. `scripts/seed.py` + `.env.example` — register the service client**
  - Add `service-client` to the clients seeded in `seed.py`:
    - `client_id=service-client`, `client_secret=service-client-secret`
    - `allowed_grant_types=["client_credentials"]`, `allowed_scopes=["read:stats"]`
  - Add `SERVICE_CLIENT_ID`, `SERVICE_CLIENT_SECRET`, `SERVICE_CLIENT_SCOPES` to `.env.example`
