# Graph Report - .  (2026-05-25)

## Corpus Check
- 8 files · ~15,615 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 106 nodes · 128 edges · 24 communities (15 shown, 9 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_ORM Models (AST)|ORM Models (AST)]]
- [[_COMMUNITY_ORM Models (Semantic)|ORM Models (Semantic)]]
- [[_COMMUNITY_OAuth2 Flow Architecture|OAuth2 Flow Architecture]]
- [[_COMMUNITY_Auth Server & Endpoints|Auth Server & Endpoints]]
- [[_COMMUNITY_Resource Server & Skills|Resource Server & Skills]]
- [[_COMMUNITY_Token Validation Modes|Token Validation Modes]]
- [[_COMMUNITY_Database & Migration Config|Database & Migration Config]]
- [[_COMMUNITY_Auth Code Flow Security|Auth Code Flow Security]]
- [[_COMMUNITY_Client Application|Client Application]]
- [[_COMMUNITY_AI Tooling & Graphify|AI Tooling & Graphify]]
- [[_COMMUNITY_Project Documentation|Project Documentation]]
- [[_COMMUNITY_Docker Infrastructure|Docker Infrastructure]]
- [[_COMMUNITY_SQLAlchemy Integration|SQLAlchemy Integration]]
- [[_COMMUNITY_Claude Code Hooks|Claude Code Hooks]]
- [[_COMMUNITY_Local Permissions Config|Local Permissions Config]]
- [[_COMMUNITY_Service Client CLI|Service Client CLI]]
- [[_COMMUNITY_Resource Owner|Resource Owner]]
- [[_COMMUNITY_Docker Network|Docker Network]]
- [[_COMMUNITY_Testing Framework|Testing Framework]]
- [[_COMMUNITY_Code Style|Code Style]]
- [[_COMMUNITY_Client Credentials Security|Client Credentials Security]]
- [[_COMMUNITY_Refresh Token Handling|Refresh Token Handling]]

## God Nodes (most connected - your core abstractions)
1. `Authorization Server` - 15 edges
2. `Authorization Code Flow` - 11 edges
3. `OAuthClient Model` - 10 edges
4. `Client Credentials Flow` - 8 edges
5. `oauth2-debug-flow Skill` - 7 edges
6. `User Model` - 7 edges
7. `Resource Server` - 6 edges
8. `Client Application` - 6 edges
9. `Base` - 6 edges
10. `AuthorizationCode Model` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Authorization Code Flow` --references--> `User Model`  [INFERRED]
  README.md → auth-server/models.py
- `Client Credentials Flow` --references--> `OAuthClient Model`  [INFERRED]
  README.md → auth-server/models.py
- `PLAN.md - Client Credentials Implementation Plan` --references--> `OAuthClient Model`  [EXTRACTED]
  PLAN.md → auth-server/models.py
- `Authorization Code Flow` --references--> `AuthorizationCode Model`  [INFERRED]
  README.md → auth-server/models.py
- `OAuthClient Database Model` --semantically_similar_to--> `auth-server/models.py`  [INFERRED] [semantically similar]
  .github/skills/oauth2-debug-flow.md → AGENTS.md

## Hyperedges (group relationships)
- **Core OAuth2 Database Models (User, OAuthClient, AuthorizationCode, Token)** — authserver_models_user, authserver_models_oauthclient, authserver_models_authorizationcode, authserver_models_token [EXTRACTED 1.00]
- **Authorization Code Flow: Client App, Auth Server, Resource Server** — concept_client_app, concept_authorization_server, concept_resource_server [EXTRACTED 1.00]
- **Alembic Migration Syncs with SQLAlchemy Models and Config** — migrations_env_target_metadata, authserver_models_base, authserver_config_database_url [EXTRACTED 1.00]

## Communities (24 total, 9 thin omitted)

### Community 0 - "ORM Models (AST)"
Cohesion: 0.31
Nodes (11): AuthorizationCode Model, SQLAlchemy DeclarativeBase, OAuthClient Model, Token Model, User Model, @require_client_token Decorator, @require_oauth2 Decorator, Resource Server (FastAPI, port 5002) (+3 more)

### Community 1 - "ORM Models (Semantic)"
Cohesion: 0.24
Nodes (9): Base, OAuthClient, A registered OAuth2 client application.      allowed_grant_types controls which, Issued access token.      user_id is NULL for client_credentials tokens — the to, Token, User, bool, DeclarativeBase (+1 more)

### Community 2 - "OAuth2 Flow Architecture"
Cohesion: 0.18
Nodes (12): Short-lived code issued at /authorize, exchanged for a token at /token.     Only, Authorization Code Flow, Authorization Server (FastAPI, port 5000), Client Application (Flask, port 5001), Client Credentials Flow, PKCE (Proof Key for Code Exchange), Refresh Token, Scope Restriction (+4 more)

### Community 3 - "Auth Server & Endpoints"
Cohesion: 0.20
Nodes (10): Alembic (Database Migrations), auth-server/routes.py, auth-server/security.py, Authorization Server, /.well-known/oauth-metadata Endpoint, PostgreSQL Database, /refresh Endpoint, Refresh Token (+2 more)

### Community 4 - "Resource Server & Skills"
Cohesion: 0.33
Nodes (7): resource-server/routes.py, resource-server/security.py, Resource Server, GitHub Skills Set (.github/skills/), FastAPI Framework, oauth2-add-endpoint Skill, @require_oauth2 Decorator

### Community 5 - "Token Validation Modes"
Cohesion: 0.40
Nodes (6): /introspect Endpoint, JWT Access Token, JWT Access Token, TOKEN_VALIDATION_MODE Environment Variable, Token Introspection Mode, JWT Validation Mode (local signature check)

### Community 6 - "Database & Migration Config"
Cohesion: 0.50
Nodes (4): DATABASE_URL Config, run_migrations_offline(), run_migrations_online(), target_metadata (Base.metadata)

### Community 7 - "Auth Code Flow Security"
Cohesion: 0.83
Nodes (4): /authorize Endpoint, PKCE (Proof Key for Code Exchange), State Parameter (CSRF Protection), oauth2-debug-flow Skill

### Community 8 - "Client Application"
Cohesion: 0.50
Nodes (4): Client Application, client-app/auth.py, client-app/routes.py, Flask Framework

### Community 9 - "AI Tooling & Graphify"
Cohesion: 0.67
Nodes (4): Graphify Knowledge Graph Usage Rules, Claude Code Settings (PreToolUse Hook), .claude/CLAUDE.md Graphify Trigger Rule, Graphify Skill (SKILL.md)

### Community 10 - "Project Documentation"
Cohesion: 0.50
Nodes (4): OAuth2 Implementation Project Overview, Development Workflow, AGENTS.md AI Agent Guide, OAuth2 Authorization Code Flow

### Community 11 - "Docker Infrastructure"
Cohesion: 0.50
Nodes (4): auth-server Docker Service, client-app Docker Service, postgres Docker Service, resource-server Docker Service

### Community 12 - "SQLAlchemy Integration"
Cohesion: 0.67
Nodes (3): auth-server/models.py, SQLAlchemy ORM, OAuthClient Database Model

## Knowledge Gaps
- **30 isolated node(s):** `PreToolUse`, `Claude Code Settings (PreToolUse Hook)`, `Resource Owner`, `auth-server/security.py`, `auth-server/routes.py` (+25 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Authorization Server` connect `Auth Server & Endpoints` to `Resource Server & Skills`, `Token Validation Modes`, `Auth Code Flow Security`, `Client Application`, `SQLAlchemy Integration`?**
  _High betweenness centrality (0.281) - this node is a cross-community bridge._
- **Why does `Authorization Code Flow` connect `OAuth2 Flow Architecture` to `ORM Models (AST)`, `ORM Models (Semantic)`, `Token Validation Modes`?**
  _High betweenness centrality (0.261) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Authorization Code Flow` (e.g. with `User Model` and `AuthorizationCode Model`) actually correct?**
  _`Authorization Code Flow` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `OAuthClient Model` (e.g. with `Client Credentials Flow` and `@require_client_token Decorator`) actually correct?**
  _`OAuthClient Model` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Client Credentials Flow` (e.g. with `OAuthClient Model` and `Authorization Code Flow`) actually correct?**
  _`Client Credentials Flow` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `PreToolUse`, `Claude Code Settings (PreToolUse Hook)`, `Resource Owner` to the rest of the system?**
  _38 weakly-connected nodes found - possible documentation gaps or missing edges._