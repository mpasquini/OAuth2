# Contributing to OAuth2 Implementation

## Getting Started

1. **Clone and setup**
   ```bash
   git clone <repo-url>
   cd OAuth2
   make install
   make setup-env
   make up
   ```

2. **Verify everything works**
   ```bash
   make health
   make test
   ```

## Development Workflow

### Before you start
- Create a feature branch: `git checkout -b feature/your-feature-name`
- Keep changes focused on a single concern
- Write tests for new features

### Code Style

#### Python
- Use **PEP 8** formatting
- Line length: 100 characters max (black formatter)
- Type hints required for function signatures
- Docstrings for all public functions (Google style)

Example:
```python
def get_user_by_id(user_id: int) -> Optional[User]:
    """Retrieve a user by their ID.
    
    Args:
        user_id: The unique user identifier
        
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()
```

#### Git Commits
- Use present tense: "Add feature" not "Added feature"
- Keep commits atomic and logical
- Reference issues: "Fix #42: Add PKCE support"
- Commit message format:
  ```
  Type: Brief description (50 chars max)
  
  Longer explanation if needed, wrapped at 72 chars.
  Can span multiple paragraphs.
  
  Fixes #123
  ```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Testing Requirements

- Write tests for all new features
- Minimum 80% code coverage
- Run tests before pushing: `make test`
- Test edge cases and error scenarios

Example test:
```python
def test_token_expiry():
    """Test that expired tokens are rejected."""
    expired_token = create_expired_token()
    with pytest.raises(TokenExpiredError):
        validate_token(expired_token)
```

### Adding a New Feature

#### 1. Add Protected Endpoint (Resource Server)

```python
# resource-server/routes.py
from security import require_oauth2

@app.get("/api/user/subscription")
@require_oauth2
async def get_subscription(request):
    """Get user subscription details."""
    user = request.oauth2_user
    return {"tier": "premium", "expires": "2025-12-31"}
```

Then test it:
```python
def test_get_subscription_with_token():
    token = create_test_token(user_id=1)
    response = client.get(
        "/api/user/subscription",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["tier"] == "premium"
```

#### 2. Add New OAuth2 Grant Type

```python
# auth-server/security.py
def generate_device_code_token(device_id: str) -> Dict:
    """Generate token for device flow."""
    payload = {
        "sub": device_id,
        "type": "device",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# auth-server/routes.py
@app.post("/device")
async def device_flow(request: DeviceFlowRequest):
    """Initiate device authorization flow."""
    device_code = generate_device_code_token(request.device_id)
    return {"device_code": device_code, "expires_in": 3600}
```

#### 3. Update Client App Flow

```python
# client-app/auth.py
def handle_device_flow():
    """Initiate device authorization flow."""
    response = requests.post(
        f"{AUTH_SERVER_URL}/device",
        json={"device_id": get_device_id()}
    )
    device_code = response.json()["device_code"]
    session["device_code"] = device_code
    return poll_for_token(device_code)
```

## Database Schema Changes

When modifying database models:

1. **Create migration**
   ```bash
   docker-compose exec auth-server alembic revision --autogenerate -m "Add subscription column"
   ```

2. **Review generated migration** in `migrations/versions/`

3. **Test migration**
   ```bash
   make migrate
   make test
   ```

4. **Commit both** model and migration files

## Security Considerations

- Never commit `.env` with real credentials
- Don't log sensitive data (tokens, passwords)
- Use environment variables for secrets
- Validate all user input
- Validate HTTPS in production
- Keep dependencies updated

## Documentation

- Update [README.md](README.md) for user-facing changes
- Update [AGENTS.md](AGENTS.md) if changing architecture or conventions
- Add docstrings for complex functions
- Include examples for new features

## Pull Request Process

1. **Update your branch**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run tests and linting**
   ```bash
   make test
   make coverage
   ```

3. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **PR checklist**
   - [ ] Tests pass locally
   - [ ] Code follows style guide
   - [ ] Docstrings added/updated
   - [ ] README/AGENTS.md updated if needed
   - [ ] No debug code left behind
   - [ ] Commits are logical and well-described

5. **Address review feedback**
   - Don't rewrite history after PR creation
   - Use `git commit --amend` for small fixes, new commits for changes
   - Re-request review after updates

## Common Tasks

### Run linter
```bash
flake8 auth-server/ resource-server/ client-app/
black --check auth-server/ resource-server/ client-app/
```

### Format code
```bash
black auth-server/ resource-server/ client-app/
```

### Check types
```bash
mypy auth-server/ resource-server/ client-app/
```

### Debug a service
```bash
make logs-auth
# or specific service
docker-compose logs -f resource-server
```

### Reset database
```bash
make clean
make up
make migrate
make seed
```

## Troubleshooting

### Tests fail locally but pass CI
- Check Python version: `python --version` (should be 3.9+)
- Check dependencies: `make install`
- Reset environment: `make clean-all` then `make up`

### Port already in use
```bash
# Find what's using the port (e.g., 5000)
lsof -i :5000

# Kill the process
kill -9 <PID>
```

### Database locked
```bash
make clean
make up
```

## Questions?

- Check [AGENTS.md](AGENTS.md) for architecture details
- Review [README.md](README.md) for setup help
- Look at existing tests for examples
- Ask in discussions or create an issue

---

Thanks for contributing! 🎉
