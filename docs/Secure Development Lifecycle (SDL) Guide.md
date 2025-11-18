# Security Development Guide

**Library of Babble - Secure Development Lifecycle (SDL) Standards**

Version: 1.0
Last Updated: 2025-11-18
Status: Active

---

## Table of Contents

1. [Overview](#overview)
2. [Security Principles](#security-principles)
3. [Input Validation & Sanitization](#input-validation--sanitization)
4. [Output Encoding](#output-encoding)
5. [Authentication & Authorization](#authentication--authorization)
6. [Database Security](#database-security)
7. [File Operations](#file-operations)
8. [API Security](#api-security)
9. [Error Handling](#error-handling)
10. [Security Headers](#security-headers)
11. [Code Review Checklist](#code-review-checklist)
12. [Testing Requirements](#testing-requirements)

---

## Overview

This guide outlines security requirements and best practices for all development work on Library of Babble. **All new features, bug fixes, and changes must comply with these standards.**

### Goals

- Prevent common web vulnerabilities (OWASP Top 10)
- Maintain defense-in-depth security posture
- Ensure consistent security practices across codebase
- Enable secure development without slowing down delivery

### Scope

This guide applies to:
- All Python backend code (Flask routes, services, utilities)
- All frontend JavaScript code
- Database queries and migrations
- File upload/download functionality
- External API integrations
- Configuration and deployment

---

## Security Principles

### Defense in Depth

Apply multiple layers of security controls. Never rely on a single protection mechanism.

**Example:**
```python
# Layer 1: User must be authenticated
@login_required
def upload_artwork():
    # Layer 2: Validate file type
    if not allowed_file(filename):
        abort(400)

    # Layer 3: Sanitize filename
    safe_filename = secure_filename(filename)

    # Layer 4: Validate final path
    if not validate_file_path(base_dir, final_path):
        abort(400)
```

### Principle of Least Privilege

Grant minimum necessary permissions. Users, processes, and code should only access what they need.

### Fail Securely

When errors occur, fail in a secure state. Never expose sensitive information in error messages.

**Good:**
```python
except Exception as e:
    app.logger.error(f"Database error: {str(e)}", exc_info=True)
    return "An error occurred", 500
```

**Bad:**
```python
except Exception as e:
    return f"Database error: {str(e)}", 500  # Leaks internal details
```

### Security by Default

Secure configurations should be the default. Insecure options require explicit opt-in.

---

## Input Validation & Sanitization

### Rule: Validate All Inputs

**ALWAYS validate user input before processing.** This includes:
- Form data
- URL parameters
- JSON payloads
- File uploads
- HTTP headers

### HTML Content (Reviews, Comments)

**When to use:** User-submitted content that may contain HTML formatting

**How to implement:**

```python
from app.utils.security import sanitize_html

# In your route handler
user_review = request.form.get('review_text')
safe_review = sanitize_html(user_review)

# Store sanitized version
review.review_text = safe_review
db.session.commit()
```

**Allowed tags:** `<p>`, `<br>`, `<strong>`, `<em>`, `<u>`, `<a>`, `<ul>`, `<ol>`, `<li>`, `<blockquote>`

**Forbidden:** `<script>`, `<iframe>`, `<object>`, `<embed>`, event handlers

### File Paths and Directory Names

**When to use:** Any user-provided path or directory name

**How to implement:**

```python
from app.utils.security import sanitize_directory_name, validate_file_path
from pathlib import Path

# Sanitize directory/filename
safe_dirname = sanitize_directory_name(user_provided_name)
if not safe_dirname:
    return jsonify({'error': 'Invalid directory name'}), 400

# Validate final path
base_dir = Path('static/images/artists')
final_path = base_dir / safe_dirname / filename

if not validate_file_path(base_dir, final_path):
    return jsonify({'error': 'Invalid file path'}), 400
```

### URL Validation (Redirects)

**When to use:** Any redirect using user-provided URLs

**How to implement:**

```python
from app.utils.security import is_safe_url

next_page = request.args.get('next')
if next_page and is_safe_url(next_page):
    return redirect(next_page)
else:
    return redirect(url_for('main.home'))
```

**Never do:**
```python
# DANGEROUS - Open redirect vulnerability
return redirect(request.args.get('next'))
```

### Data Type Validation

**Always validate data types match expectations:**

```python
# Good
try:
    page_number = int(request.args.get('page', 1))
    if page_number < 1:
        page_number = 1
except ValueError:
    page_number = 1

# Bad
page_number = request.args.get('page', 1)  # Could be string, causing errors
```

---

## Output Encoding

### Template Rendering

**Default:** Jinja2 auto-escapes by default. **DO NOT disable this.**

**Good:**
```jinja
<p>{{ user_review }}</p>  <!-- Auto-escaped -->
```

**Dangerous:**
```jinja
<p>{{ user_review|safe }}</p>  <!-- ONLY use if already sanitized -->
```

**Rule:** Only use `|safe` filter if content was sanitized with `sanitize_html()` before storage.

### JSON Responses

**Use Flask's `jsonify()` for all JSON responses:**

```python
# Good
return jsonify({'message': user_input, 'status': 'success'})

# Bad
return f'{{"message": "{user_input}"}}'  # Manual JSON is dangerous
```

---

## Authentication & Authorization

### Route Protection

**All routes except login/register MUST be protected:**

```python
from flask_login import login_required

@books_bp.route('/add', methods=['POST'])
@login_required  # REQUIRED
def add_book():
    # Route implementation
```

### Password Handling

**NEVER store plaintext passwords. Always use hashing:**

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Storing password
hashed_password = generate_password_hash(password)
user.password = hashed_password

# Verifying password
if check_password_hash(user.password, provided_password):
    login_user(user)
```

### Session Security

**Configure secure session cookies:**

```python
# In config.py
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
SESSION_COOKIE_SECURE = True    # HTTPS only (production)
SESSION_COOKIE_SAMESITE = 'Lax' # CSRF protection
```

---

## Database Security

### ORM Queries (Preferred)

**ALWAYS use SQLAlchemy ORM when possible:**

```python
# Good - Parameterized automatically
user = User.query.filter_by(username=username).first()
books = Books.query.filter(Books.title.like(f"%{search}%")).all()
```

### Raw SQL (When Necessary)

**If raw SQL is required, use parameterized queries:**

```python
# Good - Parameterized
db.session.execute(
    db.text("SELECT * FROM users WHERE username = :name"),
    {"name": username}
)

# DANGEROUS - SQL Injection
db.session.execute(
    db.text(f"SELECT * FROM users WHERE username = '{username}'")
)
```

### Table/Column Names in Raw SQL

**PostgreSQL doesn't support parameters for table/column names. Use whitelists:**

```python
def reset_sequence(table_name):
    # Whitelist validation
    ALLOWED_TABLES = {'books', 'reviews', 'collections'}

    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Table {table_name} not in whitelist")

    # Now safe to use in query
    db.session.execute(db.text(
        f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
        f"COALESCE((SELECT MAX(id) FROM {table_name}), 1), true);"
    ))
```

**Updating whitelists:**
- Add new tables to `ALLOWED_TABLES` set as needed
- Document why each table is in the whitelist
- Never accept user input for table/column names

---

## File Operations

### File Uploads

**Required validations for all file uploads:**

1. **File Type Validation**
```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

2. **Filename Sanitization**
```python
from werkzeug.utils import secure_filename

filename = secure_filename(uploaded_file.filename)
```

3. **File Size Limits**
```python
# In config.py
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
```

4. **Path Validation**
```python
from app.utils.security import validate_file_path

if not validate_file_path(base_dir, final_path):
    abort(400)
```

### File Downloads

**Validate file paths before serving:**

```python
from pathlib import Path

def serve_file(filename):
    base_dir = Path('static/uploads')
    file_path = base_dir / filename

    # Ensure path is within base directory
    if not validate_file_path(base_dir, file_path):
        abort(404)

    if not file_path.exists():
        abort(404)

    return send_file(file_path)
```

---

## API Security

### CSRF Protection

**All POST/PUT/DELETE requests MUST include CSRF token:**

**Backend (automatic):**
```python
# Flask-WTF handles this automatically if initialized
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()
csrf.init_app(app)
```

**Frontend (AJAX):**
```javascript
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

fetch('/api/endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()  // REQUIRED
    },
    body: JSON.stringify(data)
})
```

**Frontend (Forms):**
```jinja
<form method="POST">
    {{ form.csrf_token }}  <!-- REQUIRED -->
    <!-- form fields -->
</form>
```

### Rate Limiting

**Consider adding rate limiting for sensitive endpoints:**

```python
# Future implementation recommendation
from flask_limiter import Limiter

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Prevent brute force
def login():
    # Login logic
```

---

## Error Handling

### Production Error Pages

**Never expose stack traces or internal details in production:**

```python
@app.errorhandler(500)
def internal_error(error):
    # Log the full error
    app.logger.error(f"Server error: {str(error)}", exc_info=True)

    # Roll back database session
    db.session.rollback()

    # Return generic error page (NO details)
    return render_template('500.html'), 500
```

### Logging

**Log security events appropriately:**

```python
# Good - Log without sensitive data
app.logger.warning(f"Failed login attempt for user: {username}")

# Bad - Don't log passwords, tokens, etc.
app.logger.info(f"User {username} logged in with password {password}")
```

**Security events to log:**
- Failed login attempts
- Permission denied errors
- File upload rejections
- CSRF validation failures
- SQL errors (without exposing data)

---

## Security Headers

### Current Implementation

Security headers are automatically added to all responses via `register_security_headers()` in `app/__init__.py`.

### When Adding External Resources

**If you need to load resources from a new external domain, update CSP:**

```python
# In app/__init__.py, register_security_headers()

csp = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://new-cdn.com; "  # Add here
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    # ... rest of CSP
)
```

**Important:**
- Only add trusted domains
- Be as specific as possible
- Document why each domain is needed
- Test thoroughly after changes

### Avoiding 'unsafe-inline'

**Current state:** We use `'unsafe-inline'` for scripts/styles.

**Future improvement:** Use nonces or hashes instead:

```python
# Generate nonce per request
nonce = generate_nonce()
csp = f"script-src 'self' 'nonce-{nonce}';"

# In template
<script nonce="{{ nonce }}">
    // Inline script
</script>
```

---

## Code Review Checklist

Use this checklist when reviewing pull requests:

### Input Validation
- [ ] All user inputs are validated
- [ ] HTML content is sanitized before storage
- [ ] File paths are sanitized and validated
- [ ] Redirect URLs are validated
- [ ] Data types are checked

### Database
- [ ] SQLAlchemy ORM used when possible
- [ ] Raw SQL uses parameterized queries
- [ ] Table/column names use whitelist validation
- [ ] No string concatenation in SQL

### Authentication
- [ ] Routes are protected with `@login_required`
- [ ] Passwords are hashed, never stored plaintext
- [ ] Session cookies configured securely

### CSRF Protection
- [ ] All forms include `{{ form.csrf_token }}`
- [ ] All AJAX POST/PUT/DELETE include `X-CSRFToken` header

### File Operations
- [ ] File types are validated
- [ ] Filenames are sanitized
- [ ] Paths are validated against traversal
- [ ] File size limits are enforced

### Error Handling
- [ ] Errors are logged appropriately
- [ ] Production errors don't expose details
- [ ] Database session rolled back on error

### Output Encoding
- [ ] Templates use auto-escaping (default)
- [ ] `|safe` filter only used with sanitized content
- [ ] JSON responses use `jsonify()`

### Security Headers
- [ ] New external resources added to CSP
- [ ] No inline scripts/styles without nonces (future)

---

## Testing Requirements

### Security Testing Checklist

Before deploying new features:

#### 1. CSRF Testing
```bash
# Test that CSRF protection works
curl -X POST http://localhost:5000/books/add \
  -H "Content-Type: application/json" \
  -d '{"title": "Test"}' \
  # Should fail without CSRF token
```

#### 2. XSS Testing
```python
# Test HTML sanitization
test_input = '<script>alert("XSS")</script><p>Safe content</p>'
result = sanitize_html(test_input)
assert '<script>' not in result
assert '<p>Safe content</p>' in result
```

#### 3. Path Traversal Testing
```python
# Test path validation
from app.utils.security import sanitize_directory_name

assert sanitize_directory_name('../../../etc/passwd') is None
assert sanitize_directory_name('valid_name') == 'valid_name'
assert sanitize_directory_name('name/../traversal') is None
```

#### 4. SQL Injection Testing
```python
# Test whitelist validation
from scripts.etl.books_etl import reset_sequence

# Should work
reset_sequence('books')

# Should raise ValueError
try:
    reset_sequence('users; DROP TABLE books;')
    assert False, "Should have raised ValueError"
except ValueError:
    pass
```

#### 5. Authentication Testing
```python
# Test login required
response = client.get('/books/add')
assert response.status_code == 302  # Redirect to login
assert '/login' in response.location
```

### Manual Security Testing

**Before each release:**

1. **Test login/logout flow**
   - Verify session invalidation
   - Check password verification
   - Test "remember me" functionality

2. **Test file uploads**
   - Try uploading non-image files
   - Try path traversal in filenames
   - Verify file size limits

3. **Test input validation**
   - Submit forms with XSS payloads
   - Try SQL injection in search fields
   - Test redirect parameter manipulation

4. **Check browser console**
   - No CSP violations
   - No mixed content warnings
   - No JavaScript errors

---

## Common Vulnerabilities Reference

### OWASP Top 10 Coverage

| Vulnerability | Our Protection | Implementation |
|--------------|---------------|----------------|
| **A01: Broken Access Control** | `@login_required` decorator | All routes protected |
| **A02: Cryptographic Failures** | Password hashing, HTTPS | `generate_password_hash()` |
| **A03: Injection** | ORM + parameterized queries + whitelists | SQLAlchemy, `sanitize_html()` |
| **A04: Insecure Design** | Defense in depth, fail securely | Multiple validation layers |
| **A05: Security Misconfiguration** | Debug disabled, security headers | `config.py`, `register_security_headers()` |
| **A06: Vulnerable Components** | Regular updates | Requirements.txt versioning |
| **A07: Auth Failures** | Flask-Login, password hashing | Session management |
| **A08: Data Integrity Failures** | CSRF protection, input validation | Flask-WTF |
| **A09: Logging Failures** | Security event logging | App logger |
| **A10: SSRF** | URL validation | `is_safe_url()` |

---

## Quick Reference

### Security Utility Functions

Located in `app/utils/security.py`:

| Function | Purpose | Usage |
|----------|---------|-------|
| `sanitize_html(text)` | Clean user HTML | Reviews, comments |
| `is_safe_url(url)` | Validate redirect URLs | Login redirects |
| `sanitize_directory_name(name)` | Clean directory names | File uploads |
| `validate_file_path(base, path)` | Prevent path traversal | File operations |
| `validate_script_path(script)` | Whitelist subprocess scripts | ETL, background jobs |
| `validate_script_args(script, args)` | Whitelist script arguments | ETL, background jobs |
| `validate_password(password)` | Password strength check | Registration |
| `validate_uploaded_file(file)` | File upload validation | Image uploads |

### Import Statements

```python
# For routes with HTML content
from app.utils.security import sanitize_html

# For routes with redirects
from app.utils.security import is_safe_url

# For routes with file uploads
from app.utils.security import (
    sanitize_directory_name,
    validate_file_path,
    validate_uploaded_file
)

# For authentication
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
```

---

## Getting Help

### Questions?

- **Security concern?** Escalate immediately, don't merge
- **Not sure about approach?** Ask for security review
- **Found vulnerability?** Create private security issue

### Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/faq/security.html)
- Internal: `docs/ignore/` security implementation docs

---

## Document Updates

This document should be updated when:
- New security vulnerabilities are discovered
- Security utilities are added/changed
- External security requirements change
- Major framework updates occur

**Review Schedule:** Quarterly or after security incidents

---

**Last Updated:** 2025-11-18
**Version:** 1.0
**Owner:** Development Team
