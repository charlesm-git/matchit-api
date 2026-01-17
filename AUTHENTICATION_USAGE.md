# Authentication System Usage Guide

## Overview

JWT-based authentication using:

- **argon2-cffi** for password hashing
- **PyJWT** for token generation/verification

## Installation

Add to `requirements.txt`:

```
argon2-cffi
PyJWT
```

Install:

```bash
pip install argon2-cffi PyJWT
```

## Configuration

**IMPORTANT**: Before production, change the secret key in `helper.py`:

```python
SECRET_KEY = "your-secret-key-change-this-in-production"
```

Use a strong random key (generate with `openssl rand -hex 32`).

## API Endpoints

### 1. Signup (Register New Account)

```http
POST /auth/signup
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securePassword123"
}
```

**Response (201):**

```json
{
  "id": 1,
  "username": "john_doe"
}
```

**Error (400):**

```json
{
  "detail": "Username already exists"
}
```

### 2. Login (Get JWT Token)

```http
POST /auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securePassword123"
}
```

**Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error (401):**

```json
{
  "detail": "Invalid username or password"
}
```

### 3. Get Current User Info

```http
GET /auth/me
Authorization: Bearer <your_token>
```

**Response (200):**

```json
{
  "id": 1,
  "username": "john_doe"
}
```

## Protecting Your Endpoints

### Basic Protection

Use the `get_current_account` dependency:

```python
from fastapi import APIRouter, Depends
from dependencies import get_current_account
from models.account import Account

router = APIRouter()

@router.get("/protected")
def protected_route(account: Account = Depends(get_current_account)):
    return {
        "message": f"Hello {account.username}",
        "account_id": account.id
    }
```

### Example: User-Specific Data

```python
@router.get("/my-data")
def get_my_data(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db_session)
):
    # Access account.id to fetch user-specific data
    user_data = db.query(UserData).filter(UserData.account_id == account.id).all()
    return {"data": user_data}
```

## Frontend Integration

### 1. Login Flow

```javascript
// Login request
const response = await fetch("/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    username: "john_doe",
    password: "password123",
  }),
});

const { access_token } = await response.json();

// Store token (choose one method)
localStorage.setItem("token", access_token); // Simple but vulnerable to XSS
// OR
sessionStorage.setItem("token", access_token); // Cleared on tab close
// OR (recommended for production)
// Store in httpOnly cookie via backend
```

### 2. Making Authenticated Requests

```javascript
const token = localStorage.getItem("token");

const response = await fetch("/protected-endpoint", {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
```

### 3. Logout

```javascript
// Call logout endpoint (optional)
await fetch("/auth/logout", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

// Remove token
localStorage.removeItem("token");
```

### 4. Handle 401 Errors

```javascript
const response = await fetch("/protected", {
  headers: { Authorization: `Bearer ${token}` },
});

if (response.status === 401) {
  // Token expired or invalid
  localStorage.removeItem("token");
  // Redirect to login page
  window.location.href = "/login";
}
```

## Token Expiration

Default: **30 minutes** (configured in `helper.py`)

Change via:

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
```

Or per-token:

```python
from datetime import timedelta
from helper import create_access_token

# Custom expiration for specific use case
token = create_access_token(
    data={"sub": str(account.id)},
    expires_delta=timedelta(hours=24)
)
```

## Security Best Practices

1. **Secret Key**: Use environment variable:

   ```python
   import os
   SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-dev-key")
   ```

2. **HTTPS Only**: Always use HTTPS in production

3. **Token Storage**:
   - Best: httpOnly cookies (immune to XSS)
   - Acceptable: Memory/sessionStorage
   - Avoid: localStorage (XSS risk)

4. **Password Requirements**: Enforce in schema:

   ```python
   password: str = Field(..., min_length=12, regex="^(?=.*[A-Za-z])(?=.*\\d)")
   ```

5. **Rate Limiting**: Add to login endpoint to prevent brute force

## Troubleshooting

**401 Unauthorized on Protected Route:**

- Check token is included: `Authorization: Bearer <token>`
- Verify token not expired (check `exp` claim)
- Ensure account still exists in database

**Invalid Token:**

- Token may be malformed
- Secret key mismatch
- Algorithm mismatch

**Test Token Decoding:**

```python
from helper import decode_access_token

payload = decode_access_token("your_token_here")
print(payload)  # None if invalid, dict if valid
```
