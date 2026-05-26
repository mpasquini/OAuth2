# Graph Report - .  (2026-05-26)

## Corpus Check
- 12 files · ~23,507 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 373 nodes · 544 edges · 50 communities (28 shown, 22 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 76 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Auth Code Flow & Refresh|Auth Code Flow & Refresh]]
- [[_COMMUNITY_OAuth2 Models & Permissions|OAuth2 Models & Permissions]]
- [[_COMMUNITY_AGENTS  Docs Corpus|AGENTS / Docs Corpus]]
- [[_COMMUNITY_Client App Auth Flow|Client App Auth Flow]]
- [[_COMMUNITY_Database & Authorize Endpoints|Database & Authorize Endpoints]]
- [[_COMMUNITY_Auth Server Config|Auth Server Config]]
- [[_COMMUNITY_Auth Server Routes (Semantic)|Auth Server Routes (Semantic)]]
- [[_COMMUNITY_Client App Tests|Client App Tests]]
- [[_COMMUNITY_Resource Server Tests|Resource Server Tests]]
- [[_COMMUNITY_Token Validation & Introspection|Token Validation & Introspection]]
- [[_COMMUNITY_Resource Server Endpoints|Resource Server Endpoints]]
- [[_COMMUNITY_E2E Test Infrastructure|E2E Test Infrastructure]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]

## God Nodes (most connected - your core abstractions)
1. `Authorization Code Flow` - 34 edges
2. `OAuthClient` - 18 edges
3. `Client Credentials Flow` - 18 edges
4. `Authorization Server` - 15 edges
5. `Token` - 15 edges
6. `str` - 15 edges
7. `_do_auth_code_flow` - 14 edges
8. `User` - 13 edges
9. `authorize_post()` - 11 edges
10. `OAuthClient Model` - 10 edges

## Surprising Connections (you probably didn't know these)
- `_client_credentials (client_credentials flow handler)` --implements--> `Client Credentials Flow`  [INFERRED]
  auth-server/routes.py → README.md
- `Token` --references--> `Known Bug: Refresh token not persisted to DB`  [INFERRED]
  auth-server/models.py → PLAN.md
- `Authorization Code Flow` --references--> `User Model`  [INFERRED]
  README.md → auth-server/models.py
- `Authorization Code Flow` --references--> `AuthorizationCode Model`  [INFERRED]
  README.md → auth-server/models.py
- `test_callback_exchanges_code_for_token()` --references--> `Authorization Code Flow`  [INFERRED]
  tests/client_app/test_flows.py → README.md

## Hyperedges (group relationships)
- **Authorization Code + PKCE Flow (end-to-end)** — e2e_test_auth_code_flow_doauthcodeflow, auth_server_routes_authorizeget, auth_server_routes_authorizepost, auth_server_routes_tokenendpoint, auth_server_routes_authorizationcode, auth_server_models_authorizationcode, auth_server_models_user, auth_server_models_oauthclient, auth_server_models_token, concept_authcode_flow, concept_pkce [INFERRED 0.95]
- **DB schema: models + migration + seed** — auth_server_models_user, auth_server_models_oauthclient, auth_server_models_authorizationcode, auth_server_models_token, migrations_001_initialschema_upgrade, scripts_seed_main [INFERRED 0.95]
- **Docker startup sequence: compose → entrypoint → migrate → seed → uvicorn** — root_dockercompose_services, auth_server_entrypoint_sh, migrations_001_initialschema_upgrade, scripts_seed_main [INFERRED 0.85]

## Communities (50 total, 22 thin omitted)

### Community 0 - "Auth Code Flow & Refresh"
Cohesion: 0.05
Nodes (32): authorize_get (GET /authorize), refresh_endpoint (POST /refresh), Authorization Code Flow (RFC 6749 §4.1), Known Bug: Refresh token not persisted to DB, require_services (session fixture), E2E Test Constants (AUTH_SERVER_URL, RESOURCE_SERVER_URL, client IDs), generate_pkce, Shared constants and utilities for e2e tests. (+24 more)

### Community 1 - "OAuth2 Models & Permissions"
Cohesion: 0.12
Nodes (33): Base, OAuthClient, A registered OAuth2 client application.      allowed_grant_types controls which, Short-lived code issued at /authorize, exchanged for a token at /token.     Only, Issued access token.      user_id is NULL for client_credentials tokens — the to, Token, User, _authorization_code (auth_code flow handler) (+25 more)

### Community 2 - "AGENTS / Docs Corpus"
Cohesion: 0.08
Nodes (34): Alembic (Database Migrations), auth-server/models.py, auth-server/routes.py, auth-server/security.py, Authorization Server, /authorize Endpoint, Client Application, client-app/auth.py (+26 more)

### Community 3 - "Client App Auth Flow"
Cohesion: 0.09
Nodes (30): build_authorize_url(), exchange_code(), generate_pkce(), get_user_profile(), str, OAuth2 Authorization Code + PKCE helpers for the client app.  Flow summary (RFC, Return (code_verifier, code_challenge) using S256 method (RFC 7636 §4.1).      c, Build the /authorize URL the user's browser is redirected to. (+22 more)

### Community 4 - "Database & Authorize Endpoints"
Cohesion: 0.14
Nodes (28): get_db(), authorize_get(), authorize_post(), _error_page(), health(), introspect_endpoint(), _login_page(), _oauth2_error() (+20 more)

### Community 5 - "Auth Server Config"
Cohesion: 0.12
Nodes (24): ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, AUTHORIZATION_CODE_EXPIRE_MINUTES, CORS_ORIGINS, SECRET_KEY, app (FastAPI), auth-server/main.py, auth-server/routes.py (+16 more)

### Community 6 - "Auth Server Routes (Semantic)"
Cohesion: 0.13
Nodes (22): Client Credentials flow (RFC 6749 §4.4).      No user is involved. The issued to, DATABASE_URL Config, AuthorizationCode Model, SQLAlchemy DeclarativeBase, OAuthClient Model, Token Model, User Model, Authorization Server (FastAPI, port 5000) (+14 more)

### Community 7 - "Client App Tests"
Cohesion: 0.10
Nodes (18): _load(), Client app flow tests.  Covers the browser-side Authorization Code + PKCE flow:, Auth server error redirect must display an error, not crash., /profile must redirect to /login when no session token is present., Logged-in user should see decoded token claims on the profile page., /login must redirect to the auth server /authorize endpoint., state and code_verifier must be stored in the session before redirect., Mismatched state must not result in a token exchange. (+10 more)

### Community 8 - "Resource Server Tests"
Cohesion: 0.10
Nodes (10): object, _load(), Tests for the machine API endpoint (/api/service/stats).  Verifies that require_, Load a module from an explicit path and register it in sys.modules., User tokens must not access machine endpoints., Client tokens must not access user endpoints., TestServiceStats, TestUserProfile (+2 more)

### Community 9 - "Token Validation & Introspection"
Cohesion: 0.18
Nodes (18): Bearer Token Authorization, Token Introspection (RFC 7662), AUTH_SERVER_INTROSPECTION_URL, AUTH_SERVER_SECRET_KEY, TOKEN_VALIDATION_MODE, _decode_jwt(), _extract_bearer(), _introspect() (+10 more)

### Community 10 - "Resource Server Endpoints"
Cohesion: 0.17
Nodes (15): FastAPI app instance, get_service_stats(), get_user_data(), get_user_profile(), Request, Return the authenticated user's profile.     Token must have token_type='user' (, Return protected data scoped to the authenticated user., Aggregate stats endpoint for machine clients.      No user context — the caller (+7 more)

### Community 11 - "E2E Test Infrastructure"
Cohesion: 0.40
Nodes (5): Service-availability guard for e2e tests.  All e2e tests are auto-skipped when t, _reachable(), require_services(), bool, str

### Community 12 - "Community 12"
Cohesion: 0.50
Nodes (4): OAuth2 Implementation Project Overview, Development Workflow, AGENTS.md AI Agent Guide, OAuth2 Authorization Code Flow

### Community 13 - "Community 13"
Cohesion: 0.50
Nodes (4): auth-server Docker Service, client-app Docker Service, postgres Docker Service, resource-server Docker Service

### Community 14 - "Community 14"
Cohesion: 0.67
Nodes (4): Graphify Knowledge Graph Usage Rules, Claude Code Settings (PreToolUse Hook), .claude/CLAUDE.md Graphify Trigger Rule, Graphify Skill (SKILL.md)

## Knowledge Gaps
- **70 isolated node(s):** `PreToolUse`, `Claude Code Settings (PreToolUse Hook)`, `Resource Owner`, `auth-server/security.py`, `auth-server/routes.py` (+65 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Authorization Code Flow` connect `OAuth2 Models & Permissions` to `Auth Code Flow & Refresh`, `AGENTS / Docs Corpus`, `Database & Authorize Endpoints`, `Auth Server Config`, `Auth Server Routes (Semantic)`, `Client App Tests`?**
  _High betweenness centrality (0.340) - this node is a cross-community bridge._
- **Why does `Client Credentials Flow` connect `Auth Server Routes (Semantic)` to `OAuth2 Models & Permissions`, `AGENTS / Docs Corpus`, `Database & Authorize Endpoints`, `Auth Server Config`, `Token Validation & Introspection`, `Resource Server Endpoints`?**
  _High betweenness centrality (0.256) - this node is a cross-community bridge._
- **Why does `get_user_profile()` connect `Client App Auth Flow` to `AGENTS / Docs Corpus`, `Resource Server Endpoints`?**
  _High betweenness centrality (0.146) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Authorization Code Flow` (e.g. with `User Model` and `AuthorizationCode Model`) actually correct?**
  _`Authorization Code Flow` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `OAuthClient` (e.g. with `str` and `Session`) actually correct?**
  _`OAuthClient` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Client Credentials Flow` (e.g. with `OAuthClient Model` and `Authorization Code Flow`) actually correct?**
  _`Client Credentials Flow` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `Token` (e.g. with `str` and `Session`) actually correct?**
  _`Token` has 8 INFERRED edges - model-reasoned connections that need verification._