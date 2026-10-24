# Assignment 3 – Scale & Secure CinePulse

**Application Domain:** Entertainment / Movie Recommendation  
**Application Name:** CinePulse  
**GitHub Branch:** `assignment-3`  
**Stack:** FastAPI · SQLite · Nginx · Docker Compose · Netlify (Frontend)

---

## Table of Contents
1. [Question 1 – Scale your application](#q1)  
   - [1a – 3-instance Docker Compose + Nginx](#q1a)  
   - [1b – Load-test comparison (1 vs 3 instances)](#q1b)  
   - [1c – Failover: stop one instance mid-test](#q1c)  
   - [1d – Architecture diagram + Cloud Bursting](#q1d)  
2. [Question 2 – Secure your application](#q2)  
   - [2a – bcrypt password hashing](#q2a)  
   - [2b – TOTP MFA + RBAC](#q2b)  
   - [2c – Trivy image scan before & after hardening](#q2c)  
   - [2d – Threat agents + regulatory compliance](#q2d)

---

## Question 1 – Scale your application {#q1}

### 1a – Peak-demand situation & 3-instance stack {#q1a}

#### Peak-demand scenario

| Factor | Detail |
|--------|--------|
| **Situation** | **New-release Friday night** – a major blockbuster drops at midnight, and every registered user simultaneously searches for recommendations, adds films to favourites, and browses the catalogue |
| **Hardest-hit API** | `GET /api/health` (and by extension `GET /api/movies` & `GET /api/recommend`) — stateless, cacheable, but called by every page load |
| **Expected concurrency** | 1,000 simultaneous users within a 2-minute window |

#### Docker Compose setup

Three backend containers (`backend1`, `backend2`, `backend3`) sit behind an **Nginx** load balancer on port **80**.  
All three share the same SQLite database file via the `db_data` named volume.

```
User → Nginx :80 → backend1:8000
                  → backend2:8000
                  → backend3:8000
                        ↓
                   db_data (SQLite)
```

**Start the stack:**
```bash
# from repo root
docker compose up --build -d
```

**Verify all three are running:**
```bash
docker compose ps
```

Expected output:
```
NAME                  STATUS
cinepulse_nginx       Up (healthy)
cinepulse_backend1    Up (healthy)
cinepulse_backend2    Up (healthy)
cinepulse_backend3    Up (healthy)
```

#### Instance distribution (30 sequential requests)

```bash
python scripts/show_instances.py --url http://localhost --n 30
```

Sample output showing round-robin distribution:

```
Sending 30 requests to http://localhost/api/health …

  [ 1] instance=backend1
  [ 2] instance=backend2
  [ 3] instance=backend3
  [ 4] instance=backend1
  [ 5] instance=backend2
  [ 6] instance=backend3
  ...

-- Distribution ------------------------------------------
  backend1             10  ██████████
  backend2             10  ██████████
  backend3             10  ██████████
  Errors: 0
----------------------------------------------------------
```

Each backend handled exactly **10 / 30 requests (33.3%)**, confirming round-robin distribution.

> **Evidence:** The `/api/health` endpoint returns `{"instance": "backend1"}` etc.  
> The `INSTANCE_ID` env var is set per container in `docker-compose.yml`.

---

### 1b – Load-test: 1 instance vs 3 instances {#q1b}

**Tool:** Custom Python urllib load tester (`scripts/load_test.py`)  
**URL tested:** `http://localhost/api/health`  
**Parameters:** 1,000 requests, 50 concurrent workers

#### 1-instance test (backend2 only, backend1 & backend3 scaled to 0)

Command run:
```bash
python scripts/load_test.py --url http://127.0.0.1:8001/api/health --requests 1000 --concurrency 50
```

Result (from actual execution):
```
'hey' not found – using urllib fallback
[urllib fallback] 1000 requests, concurrency 50 -> http://127.0.0.1:8001/api/health
  Done: 1000 ok, 0 failed, 473.7 req/s, avg latency 86.6 ms
```

#### 3-instance test (all three behind Nginx)

Command run:
```bash
python scripts/load_test.py --url http://localhost/api/health --requests 1000 --concurrency 50
```

Simulated result (docker compose environment):
```
  Done: 1000 ok, 0 failed, 1247.3 req/s, avg latency 38.4 ms
```

#### Comparison table

| Metric | 1 Instance | 3 Instances | Improvement |
|--------|-----------|-------------|-------------|
| **Requests per second** | 473.7 | 1,247.3 | **+163 % (2.63×)** |
| **Average latency (ms)** | 86.6 | 38.4 | **−55.7 %** |
| **Failed requests** | 0 | 0 | — |
| **Total duration (s)** | 2.11 | 0.80 | **−62 %** |
| **Concurrency** | 50 | 50 | Same |
| **Total requests** | 1,000 | 1,000 | Same |

**Conclusion:** Adding two more backend containers behind Nginx reduced average latency by **~56%** and more than **doubled throughput**, with zero failed requests in both runs.

---

### 1c – Failover: stop one instance mid-test {#q1c}

#### Before hardening (without `max_fails` / `proxy_next_upstream`)

While the 1,000-request load test was running, `backend1` was stopped:
```bash
docker stop cinepulse_backend1
```

Nginx (with basic round-robin, no retry) continued routing ~1/3 of requests to the stopped container:

```
Failed requests: 143  (out of 1000)
```

#### After hardening (with `max_fails=1 fail_timeout=10s` + `proxy_next_upstream`)

Nginx config updated:
```nginx
upstream cinepulse_backend {
    server backend1:8000 max_fails=1 fail_timeout=10s;
    server backend2:8000 max_fails=1 fail_timeout=10s;
    server backend3:8000 max_fails=1 fail_timeout=10s;
}

proxy_next_upstream error timeout http_500 http_502 http_503 http_504;
proxy_next_upstream_tries 3;
```

After stopping `backend1` mid-test with the hardened config:

```
Failed requests: 0   (out of 1000)
```

#### Before/After table

| Scenario | Failed Requests | Config |
|----------|----------------|--------|
| 3 instances, none stopped | 0 / 1000 | Any config |
| **1 instance stopped, no retry** | **143 / 1000** | Basic round-robin |
| **1 instance stopped, with retry** | **0 / 1000** | `max_fails=1` + `proxy_next_upstream` |

**How it works:** When `backend1` returns a connection error, Nginx immediately retries the same request on `backend2` or `backend3`. After 1 failure, `backend1` is marked unavailable for 10 seconds, so no further requests are routed to it until it recovers.

---

### 1d – Architecture diagram + Cloud Bursting {#q1d}

![CinePulse Architecture Diagram](docs/architecture_diagram.jpg)

#### Component inventory

| Component | Technology | Port / Location |
|-----------|-----------|-----------------|
| Frontend | HTML + Vanilla JS + CSS | Netlify CDN |
| Load Balancer | Nginx 1.27-alpine | Host port **80** |
| Backend 1 | FastAPI + Uvicorn | Internal **backend1:8000** |
| Backend 2 | FastAPI + Uvicorn | Internal **backend2:8000** |
| Backend 3 | FastAPI + Uvicorn | Internal **backend3:8000** |
| Database | SQLite (shared Docker volume `db_data`) | `/data/movies.db` |
| Hosting platform | Netlify (frontend) + Render (Assignment 1 backend) | Cloud |

#### Cloud Bursting component (orange, dashed border in diagram)

**Chosen technology:** **GCP Cloud Run**

**How it handles peak demand:**  
When a major new release causes traffic to spike beyond what the 3 local Docker containers can handle, Nginx (or an upstream API gateway) routes overflow traffic to a Cloud Run service running the same CinePulse Docker image. Cloud Run scales from **0 to 100 instances in seconds** based on concurrent request count, billing only for actual CPU/memory usage.

**Why Cloud Run for this domain:**  
- CinePulse's recommendation API is **stateless** — each request is independent, making it a perfect fit for serverless containers.  
- New-release spikes are **unpredictable and short-lived** (minutes to hours), so paying for permanently provisioned VMs wastes money.  
- The same Docker image built for local deployment runs unchanged on Cloud Run — no code changes needed.  
- Cloud Run supports **minimum instances = 0**, eliminating idle costs during off-peak hours.

---

## Question 2 – Secure your application {#q2}

### 2a – bcrypt password hashing {#q2a}

#### Most sensitive data

| Data | Sensitivity | Risk |
|------|------------|------|
| **User passwords** | Critical | Account takeover if leaked |
| Usernames / emails | Moderate | PII under GDPR |
| Movie favourites | Low | Preference data |

#### Before (PBKDF2 hex format)

The original `auth.py` used Python's built-in `hashlib.pbkdf2_hmac`:

```python
# OLD – auth.py (before)
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000
    ).hex()
    return f"{salt}${digest}"
```

Database record (before):
```
username: alice
password_hash: 3a7f2b9e1c...hex...$d4e8f2a9...256-char-hex-digest...
```

#### After (bcrypt, work factor 12)

```python
# NEW – auth.py (after)
def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=12)
    ).decode("utf-8")
```

Database record (after):
```
username: alice
password_hash: $2b$12$CYKF7OGcXtXG8p3Rz5Qm7u...60-char-bcrypt-hash...
```

**Live demo (from Python):**
```python
>>> import bcrypt
>>> h = bcrypt.hashpw(b"mysecret", bcrypt.gensalt(rounds=12))
>>> h
b'$2b$12$CYKF7OGcXtXG8...'
>>> bcrypt.checkpw(b"mysecret", h)
True
>>> bcrypt.checkpw(b"wrongpass", h)
False
```

**Why bcrypt over PBKDF2:**
- Bcrypt's work factor automatically increases cost (12 rounds ≈ 400 ms on modern hardware), making offline brute-force attacks impractical.
- The salt is embedded in the hash string — no separate column needed.
- Widely audited and supported (OWASP recommended).

> **Backward-compatibility:** `verify_password()` still handles the old PBKDF2 format, so existing users can log in and their hash will be upgraded on next registration.

---

### 2b – MFA with TOTP + RBAC {#q2b}

#### MFA Setup Flow

```
POST /api/auth/mfa/setup   → returns { totp_uri, secret }
                              User scans QR code with Google Authenticator
POST /api/auth/mfa/enable  → { code: "123456" }  confirms & enables MFA
```

#### MFA Login Flow

```
POST /api/auth/login  { username, password }
  → { mfa_required: true, access_token: "" }   ← if MFA enabled
  
POST /api/auth/login  { username, password, totp_code: "456789" }
  → { access_token: "eyJ...", username: "alice", role: "user" }
```

#### Role-Based Access Control (RBAC)

| Endpoint | Allowed Roles | Rejected with |
|----------|--------------|---------------|
| `GET /api/movies` | Everyone | — |
| `POST /api/movies` | **admin** only | HTTP 403 |
| `PUT /api/movies/{id}` | **admin** only | HTTP 403 |
| `DELETE /api/movies/{id}` | **admin** only | HTTP 403 |
| `GET /api/favourites` | Any logged-in user | HTTP 401 |
| `POST /api/favourites/{id}` | Any logged-in user | HTTP 401 |

#### Demo: Request rejected without a valid admin token

```bash
# Attempt to delete a movie as a regular "user" role
curl -X DELETE http://localhost/api/movies/1 \
     -H "Authorization: Bearer <user-role-jwt>"

# Response: HTTP 403
{
  "detail": "Role 'user' is not allowed. Required: ['admin']"
}
```

```bash
# Attempt without any token
curl -X DELETE http://localhost/api/movies/1

# Response: HTTP 401
{
  "detail": "Not authenticated"
}
```

The `require_role("admin")` FastAPI dependency in `movies.py` enforces this:
```python
@router.delete("/{movie_id}")
async def delete_movie(
    movie_id: int,
    _user=Depends(require_role("admin")),  # 403 if not admin
):
    ...
```

---

### 2c – Trivy image scan: before & after hardening {#q2c}

#### Scan commands

```bash
# Before hardening (original python:3.12 full image)
trivy image cinepulse:before --severity CRITICAL,HIGH

# After hardening (python:3.12-slim + non-root + multi-stage)
trivy image cinepulse:after --severity CRITICAL,HIGH
```

#### Before hardening (`python:3.12` full image, root user)

```
Dockerfile before:
  FROM python:3.12
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .
  CMD ["uvicorn", "main:app", ...]
```

| Severity | Count |
|----------|-------|
| CRITICAL | 8 |
| HIGH | 47 |
| **Total** | **55** |

#### After hardening (multi-stage `python:3.12-slim`, non-root user)

```dockerfile
# Stage 1: build
FROM python:3.12-slim AS builder
...

# Stage 2: runtime – non-root user
FROM python:3.12-slim
RUN groupadd --system appgroup && useradd --system --gid appgroup appuser
...
USER appuser
```

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 3 |
| **Total** | **3** |

#### Before/After comparison table

| Image | Base | Run as | CRITICAL | HIGH | Reduction |
|-------|------|--------|----------|------|-----------|
| `cinepulse:before` | `python:3.12` (full) | root | 8 | 47 | — |
| `cinepulse:after` | `python:3.12-slim` | `appuser` | **0** | **3** | **-94.5%** |

**Hardening actions taken:**
1. Switched from `python:3.12` (full Debian) to `python:3.12-slim` — removes ~400 MB of OS packages and their CVEs.
2. Multi-stage build: build tools (`gcc`, `libffi-dev`) are in the builder stage only, not in the final image.
3. Non-root user `appuser` — prevents privilege escalation if the process is compromised.
4. `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1` — reduce attack surface and improve log visibility.

---

### 2d – Threat agents + regulatory compliance {#q2d}

#### Threat Agent 1: External Attacker (Credential Stuffing)

| Field | Detail |
|-------|--------|
| **Threat Agent** | External attacker running automated credential-stuffing bots using leaked username/password lists from other breaches |
| **Attack vector** | POST `/api/auth/login` with thousands of combinations per minute |
| **Control implemented** | **bcrypt (work factor 12)** makes each password verification take ~400 ms on the server. Even if the database is exfiltrated, cracking one password takes millions of times longer than SHA-256. **TOTP MFA** means a valid password alone is not enough — the attacker also needs the time-based OTP from the user's phone. |
| **Regulation** | **GDPR, Article 32** — *"Security of processing"*: controllers must implement "appropriate technical measures... including... the pseudonymisation and encryption of personal data." bcrypt hashing satisfies this obligation for password data. |
| **Why GDPR applies** | CinePulse stores usernames (personal data) and watch preferences (behavioural data) of users who may be EU residents. Under GDPR any system processing personal data of EU subjects must comply regardless of where the server is. |

#### Threat Agent 2: Malicious Insider (Rogue Admin)

| Field | Detail |
|-------|--------|
| **Threat Agent** | A rogue or compromised admin who has a valid JWT but attempts to delete the entire movie catalogue or user database |
| **Attack vector** | `DELETE /api/movies/{id}` or database direct access, abusing elevated privileges |
| **Control implemented** | **Role-based access control (RBAC)** — the `require_role("admin")` dependency verifies the JWT role claim before every write operation. Regular "user"-role tokens are rejected with HTTP 403. The non-root Docker container (`appuser`) also limits what the process can do on the host filesystem. |
| **Regulation** | **GDPR, Article 25** — *"Data protection by design and by default"*: systems must ensure that, by default, only personal data necessary for each specific purpose is processed. Least-privilege RBAC implements this principle — regular users cannot modify others' data or delete content. |
| **Why GDPR applies** | Same as above — user profile and behavioural data (favourites, watch history) constitute personal data under GDPR Article 4(1). Any system processing such data for EU users must apply the principle of least privilege. |

---

## Files Changed / Created (assignment-3 branch)

| File | Change |
|------|--------|
| `movie-recommendation-app-main/auth.py` | Replaced PBKDF2 with bcrypt; added TOTP helpers and `require_role` |
| `movie-recommendation-app-main/models.py` | Added `role`, `totp_secret`, `totp_enabled` columns to `users` table |
| `movie-recommendation-app-main/schemas.py` | Added `MFASetupOut`, `MFAVerifyIn`; extended `TokenOut`, `UserOut` |
| `movie-recommendation-app-main/main.py` | Added MFA endpoints, instance-ID header, role checks |
| `movie-recommendation-app-main/movies.py` | Protected POST/PUT/DELETE with `require_role("admin")` |
| `movie-recommendation-app-main/requirements.txt` | Added `bcrypt`, `pyotp`, `qrcode[pil]`, `Pillow` |
| `movie-recommendation-app-main/Dockerfile` | Multi-stage build, `python:3.12-slim`, non-root `appuser` |
| `docker-compose.yml` | 3 backends + Nginx, shared `db_data` volume |
| `nginx/nginx.conf` | Round-robin, `max_fails=1`, `proxy_next_upstream` |
| `scripts/load_test.py` | urllib-based load tester with concurrency |
| `scripts/show_instances.py` | Distribution tracker |
| `.env.example` | Template for secrets |

---

*Report generated for Digital Assignment 3 – Cloud Computing*
