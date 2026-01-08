# Standard Test Skill

**Purpose:** Ensure test quality according to The Standard's testing doctrine.

---

## Instructions

You are validating or creating tests according to **The Standard** testing doctrine.

### 1. Load Testing Doctrine

Read these files:
- `docs/testing.md` - Core testing rules
- `docs/testing-fastapi.md` - FastAPI patterns (if applicable)
- `docs/testing-hypothesis.md` - Property-based testing (if applicable)
- `docs/testing-playwright.md` - E2E testing (if applicable)
- `examples/testing/` - Reference implementations

### 2. Test Quality Checklist

Validate every test against:

#### Realism (MUST)
- [ ] No mocks unless testing error boundaries
- [ ] Uses real database (with transactions)
- [ ] Real HTTP calls to test server
- [ ] Actual file I/O if relevant
- [ ] Tests integration between real components

#### Determinism (MUST)
- [ ] No `sleep()` or arbitrary timeouts
- [ ] No `date.now()` or `time.time()` - use time travel
- [ ] No random data without seeds
- [ ] No network calls to external services
- [ ] Repeatable results every run

#### Documentation (MUST)
- [ ] Test name explains Given-When-Then
- [ ] Reveals system behavior through assertions
- [ ] Shows actual usage patterns
- [ ] Clear failure messages

#### Maintenance (SHOULD)
- [ ] Fast (< 1s for unit, < 5s for integration)
- [ ] Isolated (no shared mutable state)
- [ ] Focused (one behavior per test)
- [ ] Self-contained (setup within test)

### 3. Test Taxonomy

Ensure proper classification:

#### Unit Tests
- Test single function/class
- No external dependencies (DB, network, filesystem)
- Millisecond execution
- Example: `test_password_hasher()`

#### Integration Tests
- Test multiple components together
- Uses real DB, filesystem, message queues
- Seconds execution
- Example: `test_user_registration_flow()`

#### E2E Tests (Browser)
- Test full user journey
- Real browser automation
- Seconds to minutes execution
- Example: `test_complete_checkout_flow()`

### 4. Common Anti-Patterns to Flag

#### ❌ Mock Hell
```python
# BAD - Testing mocks, not behavior
@patch('service.database')
@patch('service.email')
@patch('service.auth')
def test_with_mocks(mock_db, mock_email, mock_auth):
    # This tests mock configuration, not the service
```

#### ✅ Realistic Alternative
```python
# GOOD - Test real integration
async def test_user_registration(db_session, test_client):
    response = await test_client.post("/register", json={...})
    assert response.status_code == 201
    user = await db_session.get(User, response.json()["id"])
    assert user.email == "test@example.com"
```

#### ❌ Sleeps and Polling
```python
# BAD - Non-deterministic
def test_async_task():
    trigger_task()
    time.sleep(2)  # Hope it's done?
    assert task_completed()
```

#### ✅ Deterministic Alternative
```python
# GOOD - Explicit waiting with clear conditions
async def test_async_task():
    task_id = await trigger_task()
    result = await wait_for_task_completion(task_id, timeout=5.0)
    assert result.status == "completed"
```

#### ❌ Vague Test Names
```python
# BAD - Unclear intent
def test_user():
    ...

def test_edge_case():
    ...
```

#### ✅ Documentary Names
```python
# GOOD - Clear behavior description
def test_user_registration_fails_when_email_already_exists():
    ...

def test_order_total_excludes_deleted_items():
    ...
```

### 5. Framework-Specific Patterns

#### FastAPI (Python)
```python
# Dependency override pattern (NOT mocking)
async def override_get_current_user():
    return User(id=1, email="test@example.com")

app.dependency_overrides[get_current_user] = override_get_current_user

# Test with real DB
@pytest.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield conn
        await conn.rollback()
```

#### Playwright (E2E)
```python
# Accessibility-first selectors
await page.get_by_role("button", name="Submit").click()
await page.get_by_label("Email address").fill("test@example.com")

# Test keyboard navigation
await page.keyboard.press("Tab")
await page.keyboard.press("Enter")

# Visual regression
await expect(page).to_have_screenshot()
```

### 6. Review Output Format

Structure your review as:

```markdown
## Test Quality Review

### Summary
[Overall assessment]

### Issues Found

#### Critical (Must Fix)
- [Test file:line] - [Issue description]
- [Specific violation of testing doctrine]

#### Warnings (Should Fix)
- [Non-critical quality issues]

### Recommendations
- [Suggestions for improvement]

### Coverage Analysis
- [Are key behaviors tested?]
- [Any missing test cases?]

### Verdict
- [ ] Tests meet The Standard
- [ ] Tests need revision
```

---

## When to Use This Skill

Invoke this skill when:
- Writing new tests
- Reviewing test quality in PRs
- Auditing existing test suites
- Investigating flaky tests
- Improving test coverage

---

## Example Usage

User: "Review the tests in tests/test_auth.py"
Agent: [Invokes `standard-test` skill]
Agent: [Reads test file and testing doctrine]
Agent: [Validates against quality checklist]
Agent: [Provides structured review with specific issues]
