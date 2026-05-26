# Graph Report - .  (2026-05-26)

## Corpus Check
- 31 files · ~22,057 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 320 nodes · 437 edges · 49 communities (29 shown, 20 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 37 edges (avg confidence: 0.88)
- Token cost: 34,982 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Auth Server Core|Auth Server Core]]
- [[_COMMUNITY_Client App OAuth2 Helpers|Client App OAuth2 Helpers]]
- [[_COMMUNITY_Auth Server Models & Routes|Auth Server Models & Routes]]
- [[_COMMUNITY_JWT Token Security|JWT Token Security]]
- [[_COMMUNITY_Resource Server Tests|Resource Server Tests]]
- [[_COMMUNITY_Client App Tests|Client App Tests]]
- [[_COMMUNITY_SQLAlchemy Data Models|SQLAlchemy Data Models]]
- [[_COMMUNITY_Token Validation & Introspection|Token Validation & Introspection]]
- [[_COMMUNITY_Resource Server API|Resource Server API]]
- [[_COMMUNITY_OAuthClient Permissions|OAuthClient Permissions]]
- [[_COMMUNITY_DB Seed & Bootstrap|DB Seed & Bootstrap]]
- [[_COMMUNITY_End-to-End Test Stubs|End-to-End Test Stubs]]
- [[_COMMUNITY_Auth Server Config|Auth Server Config]]
- [[_COMMUNITY_Project Documentation|Project Documentation]]
- [[_COMMUNITY_Graphify  Claude Config|Graphify / Claude Config]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 48|Community 48]]

## God Nodes (most connected - your core abstractions)
1. `Authorization Code Flow` - 26 edges
2. `Client Credentials Flow` - 17 edges
3. `Authorization Server` - 15 edges
4. `str` - 11 edges
5. `authorize_post()` - 11 edges
6. `OAuthClient Model` - 10 edges
7. `create_user_token()` - 10 edges
8. `token_endpoint()` - 10 edges
9. `refresh_endpoint()` - 10 edges
10. `introspect_endpoint()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Authorization Code Flow` --references--> `User Model`  [INFERRED]
  README.md → auth-server/models.py
- `Client Credentials Flow` --references--> `OAuthClient Model`  [INFERRED]
  README.md → auth-server/models.py
- `Authorization Code Flow` --references--> `AuthorizationCode Model`  [INFERRED]
  README.md → auth-server/models.py
- `test_callback_exchanges_code_for_token()` --references--> `Authorization Code Flow`  [INFERRED]
  tests/client_app/test_flows.py → README.md
- `test_login_redirects_to_auth_server()` --references--> `Authorization Code Flow`  [INFERRED]
  tests/client_app/test_flows.py → README.md

## Hyperedges (group relationships)
- **Authorization Code + PKCE flow components** — auth_server_routes_authorize_get, auth_server_routes_authorize_post, auth_server_routes_token_endpoint, auth_server_routes_authorization_code, auth_server_security_verify_pkce, auth_server_security_create_user_token, auth_server_security_generate_code, concept_authorization_code_flow, concept_pkce [INFERRED 0.95]
- **Client Credentials flow components** — auth_server_routes_token_endpoint, auth_server_routes_client_credentials, auth_server_security_create_client_token, concept_client_credentials_flow [INFERRED 0.95]
- **Token security helper functions** — auth_server_security_hash_value, auth_server_security_verify_value, auth_server_security_build_payload, auth_server_security_create_user_token, auth_server_security_create_client_token, auth_server_security_decode_token, auth_server_security_generate_code, auth_server_security_verify_pkce [INFERRED 0.95]
- **RFC 9700 security findings** — concept_refresh_token_not_persisted_bug, concept_pkce_downgrade_attack_bug, concept_http_redirect_uri_bug, concept_redirect_302_should_violation, concept_no_aud_claim_should_violation, concept_plaintext_access_tokens_should_violation, concept_no_refresh_token_rotation_should_violation, plan_md_rfc9700_security_review [EXTRACTED 1.00]
- **Client app flow tests** — tests_client_app_test_flows_test_login_redirects_to_auth_server, tests_client_app_test_flows_test_login_sets_session_state, tests_client_app_test_flows_test_callback_invalid_state_rejected, tests_client_app_test_flows_test_callback_exchanges_code_for_token, tests_client_app_test_flows_test_callback_error_param_shows_error, tests_client_app_test_flows_test_profile_requires_login, tests_client_app_test_flows_test_profile_shows_claims, tests_client_app_test_flows_test_logout_clears_session [EXTRACTED 1.00]
- **Authorization Code + PKCE Flow actors** — client_app_auth_generate_pkce, client_app_auth_build_authorize_url, client_app_auth_exchange_code, client_app_routes_login, client_app_routes_callback, resource_server_routes_get_user_profile, resource_server_security_require_oauth2 [INFERRED 0.95]
- **Client Credentials Flow actors** — scripts_service_client_main, scripts_service_client_post_form, resource_server_routes_get_service_stats, resource_server_security_require_client_token [INFERRED 0.95]
- **Token validation pipeline (JWT or introspection)** — resource_server_security_extract_bearer, resource_server_security_validate_token, resource_server_security_decode_jwt, resource_server_security_introspect, resource_server_config_token_validation_mode [INFERRED 0.95]
- **Client App UI template hierarchy** — template_base_html, template_index_html, template_profile_html [EXTRACTED 1.00]
- **Database bootstrap (users + clients)** — scripts_seed_main, scripts_seed_seed_users, scripts_seed_seed_clients [EXTRACTED 1.00]

## Communities (49 total, 20 thin omitted)

### Community 0 - "Auth Server Core"
Cohesion: 0.09
Nodes (41): get_db(), Short-lived code issued at /authorize, exchanged for a token at /token.     Only, authorize_get(), authorize_post(), _error_page(), introspect_endpoint(), _login_page(), _oauth2_error() (+33 more)

### Community 1 - "Client App OAuth2 Helpers"
Cohesion: 0.09
Nodes (30): build_authorize_url(), exchange_code(), generate_pkce(), get_user_profile(), str, OAuth2 Authorization Code + PKCE helpers for the client app.  Flow summary (RFC, Return (code_verifier, code_challenge) using S256 method (RFC 7636 §4.1).      c, Build the /authorize URL the user's browser is redirected to. (+22 more)

### Community 2 - "Auth Server Models & Routes"
Cohesion: 0.08
Nodes (33): Alembic (Database Migrations), auth-server/models.py, auth-server/routes.py, auth-server/security.py, Authorization Server, /authorize Endpoint, Client Application, client-app/auth.py (+25 more)

### Community 3 - "JWT Token Security"
Cohesion: 0.15
Nodes (20): ALGORITHM, SECRET_KEY, _build_payload(), create_client_token(), create_user_token(), decode_token(), generate_code(), hash_value() (+12 more)

### Community 4 - "Resource Server Tests"
Cohesion: 0.10
Nodes (10): object, _load(), Tests for the machine API endpoint (/api/service/stats).  Verifies that require_, Load a module from an explicit path and register it in sys.modules., User tokens must not access machine endpoints., Client tokens must not access user endpoints., TestServiceStats, TestUserProfile (+2 more)

### Community 5 - "Client App Tests"
Cohesion: 0.10
Nodes (18): _load(), Client app flow tests.  Covers the browser-side Authorization Code + PKCE flow:, Auth server error redirect must display an error, not crash., /profile must redirect to /login when no session token is present., Logged-in user should see decoded token claims on the profile page., /login must redirect to the auth server /authorize endpoint., state and code_verifier must be stored in the session before redirect., Mismatched state must not result in a token exchange. (+10 more)

### Community 6 - "SQLAlchemy Data Models"
Cohesion: 0.18
Nodes (16): DATABASE_URL Config, AuthorizationCode Model, SQLAlchemy DeclarativeBase, OAuthClient Model, Token Model, User Model, @require_client_token Decorator, @require_oauth2 Decorator (+8 more)

### Community 7 - "Token Validation & Introspection"
Cohesion: 0.18
Nodes (18): Bearer Token Authorization, Token Introspection (RFC 7662), AUTH_SERVER_INTROSPECTION_URL, AUTH_SERVER_SECRET_KEY, TOKEN_VALIDATION_MODE, _decode_jwt(), _extract_bearer(), _introspect() (+10 more)

### Community 8 - "Resource Server API"
Cohesion: 0.17
Nodes (15): FastAPI app instance, get_service_stats(), get_user_data(), get_user_profile(), Request, Return the authenticated user's profile.     Token must have token_type='user' (, Return protected data scoped to the authenticated user., Aggregate stats endpoint for machine clients.      No user context — the caller (+7 more)

### Community 9 - "OAuthClient Permissions"
Cohesion: 0.24
Nodes (9): Base, OAuthClient, A registered OAuth2 client application.      allowed_grant_types controls which, Issued access token.      user_id is NULL for client_credentials tokens — the to, Token, User, bool, DeclarativeBase (+1 more)

### Community 10 - "DB Seed & Bootstrap"
Cohesion: 0.39
Nodes (8): OAUTH2_CLIENT_ID (web-client), _hash(), main(), Session, str, Seed the database with test users and OAuth2 clients.  Run once after `make migr, _seed_clients(), _seed_users()

### Community 11 - "End-to-End Test Stubs"
Cohesion: 0.25
Nodes (7): End-to-end Authorization Code flow test.  Requires all services to be running (m, Simulate login → code exchange → resource access., User token must be rejected by /api/service/stats with 403., Refresh token must yield a new valid access token., test_full_authorization_code_flow(), test_token_refresh(), test_user_token_rejected_on_machine_endpoint()

### Community 12 - "Auth Server Config"
Cohesion: 0.33
Nodes (6): ACCESS_TOKEN_EXPIRE_MINUTES, AUTHORIZATION_CODE_EXPIRE_MINUTES, CORS_ORIGINS, app (FastAPI), auth-server/main.py, auth-server/routes.py

### Community 13 - "Project Documentation"
Cohesion: 0.50
Nodes (4): OAuth2 Implementation Project Overview, Development Workflow, AGENTS.md AI Agent Guide, OAuth2 Authorization Code Flow

### Community 14 - "Graphify / Claude Config"
Cohesion: 0.67
Nodes (4): Graphify Knowledge Graph Usage Rules, Claude Code Settings (PreToolUse Hook), .claude/CLAUDE.md Graphify Trigger Rule, Graphify Skill (SKILL.md)

### Community 15 - "Community 15"
Cohesion: 0.50
Nodes (4): auth-server Docker Service, client-app Docker Service, postgres Docker Service, resource-server Docker Service

## Knowledge Gaps
- **61 isolated node(s):** `PreToolUse`, `Claude Code Settings (PreToolUse Hook)`, `Resource Owner`, `auth-server/security.py`, `auth-server/routes.py` (+56 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Authorization Code Flow` connect `Auth Server Core` to `JWT Token Security`, `Client App Tests`, `SQLAlchemy Data Models`, `OAuthClient Permissions`, `End-to-End Test Stubs`?**
  _High betweenness centrality (0.312) - this node is a cross-community bridge._
- **Why does `Client Credentials Flow` connect `Auth Server Core` to `Resource Server API`, `JWT Token Security`, `SQLAlchemy Data Models`, `Token Validation & Introspection`?**
  _High betweenness centrality (0.285) - this node is a cross-community bridge._
- **Why does `get_user_profile()` connect `Client App OAuth2 Helpers` to `Resource Server API`, `Auth Server Models & Routes`?**
  _High betweenness centrality (0.169) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Authorization Code Flow` (e.g. with `User Model` and `AuthorizationCode Model`) actually correct?**
  _`Authorization Code Flow` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `Client Credentials Flow` (e.g. with `OAuthClient Model` and `Authorization Code Flow`) actually correct?**
  _`Client Credentials Flow` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `PreToolUse`, `Claude Code Settings (PreToolUse Hook)`, `Resource Owner` to the rest of the system?**
  _118 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Auth Server Core` be split into smaller, more focused modules?**
  _Cohesion score 0.09302325581395349 - nodes in this community are weakly interconnected._