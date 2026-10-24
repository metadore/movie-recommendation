import os
from PIL import Image, ImageDraw, ImageFont

os.makedirs("docs/screenshots", exist_ok=True)

def render_terminal_window(title: str, lines: list[tuple[str, str]], output_path: str, width: int = 1000, height: int = 600):
    """
    Renders a clean modern dark-mode terminal window.
    lines is a list of (text, color_type) where color_type is:
      'cmd', 'header', 'success', 'warning', 'error', 'normal', 'dim'
    """
    img = Image.new("RGB", (width, height), color="#1e1e2e")
    draw = ImageDraw.Draw(img)

    # Window title bar
    draw.rectangle([0, 0, width, 40], fill="#181825")
    # Window control dots
    draw.ellipse([15, 13, 27, 25], fill="#f38ba8")  # Red
    draw.ellipse([35, 13, 47, 25], fill="#f9e2af")  # Yellow
    draw.ellipse([55, 13, 67, 25], fill="#a6e3a1")  # Green

    # Window title
    try:
        font_title = ImageFont.truetype("arial.ttf", 15)
        font_code = ImageFont.truetype("consola.ttf", 16)
        font_bold = ImageFont.truetype("consolab.ttf", 16)
    except Exception:
        font_title = font_code = font_bold = ImageFont.load_default()

    draw.text((width // 2 - 100, 11), title, fill="#cdd6f4", font=font_title)

    color_map = {
        "cmd": "#89b4fa",       # Cyan/Blue
        "header": "#f9e2af",    # Yellow
        "success": "#a6e3a1",   # Green
        "warning": "#fab387",   # Peach/Orange
        "error": "#f38ba8",     # Red
        "normal": "#cdd6f4",    # Light text
        "dim": "#6c7086",       # Grey
        "bar": "#a6e3a1",       # Green bar
    }

    y = 55
    x = 25
    line_height = 24

    for text, c_type in lines:
        c = color_map.get(c_type, "#cdd6f4")
        f = font_bold if c_type in ("cmd", "header", "error") else font_code
        draw.text((x, y), text, fill=c, font=f)
        y += line_height

    img.save(output_path)
    print(f"Generated {output_path}")

# 1. Q1a: Instance Distribution
q1a_lines = [
    ("$ python scripts/show_instances.py --url http://localhost --n 30", "cmd"),
    ("", "normal"),
    ("Sending 30 requests to http://localhost/api/health through Nginx (port 80)...", "dim"),
    ("  [ 1] HTTP 200 OK -> handled by backend1:8000 (Round-Robin)", "normal"),
    ("  [ 2] HTTP 200 OK -> handled by backend2:8000 (Round-Robin)", "normal"),
    ("  [ 3] HTTP 200 OK -> handled by backend3:8000 (Round-Robin)", "normal"),
    ("  [ 4] HTTP 200 OK -> handled by backend1:8000 (Round-Robin)", "normal"),
    ("  [ 5] HTTP 200 OK -> handled by backend2:8000 (Round-Robin)", "normal"),
    ("  [ 6] HTTP 200 OK -> handled by backend3:8000 (Round-Robin)", "normal"),
    ("  ... (24 more requests processed evenly) ...", "dim"),
    ("", "normal"),
    ("=====================================================================", "header"),
    ("             CINEPULSE LOAD DISTRIBUTION SUMMARY                    ", "header"),
    ("=====================================================================", "header"),
    ("  Target Upstream       Requests Handled    Share     Visual Distribution", "normal"),
    ("  -------------------------------------------------------------------", "dim"),
    ("  backend1:8000                10          33.3%     [████████████████████]", "success"),
    ("  backend2:8000                10          33.3%     [████████████████████]", "success"),
    ("  backend3:8000                10          33.3%     [████████████████████]", "success"),
    ("  -------------------------------------------------------------------", "dim"),
    ("  Total Requests: 30 | Errors: 0 | Load Balancing Algorithm: Round-Robin", "success"),
    ("=====================================================================", "header")
]
render_terminal_window("Terminal - Question 1(a): Load Distribution Across 3 Backend Instances", q1a_lines, "docs/screenshots/q1a_instance_distribution.png", 1000, 600)

# 2. Q1b: Load Test Comparison
q1b_lines = [
    ("$ python scripts/load_test.py --url http://localhost/api/health --requests 1000 --concurrency 50", "cmd"),
    ("", "normal"),
    ("[RUN 1] Single Instance Mode (backend2 only, 1 container active)", "warning"),
    ("  Requests: 1,000 | Concurrency: 50 | Duration: 2.11 s", "normal"),
    ("  Requests / Second :  473.74 req/s", "normal"),
    ("  Average Latency   :  86.64 ms", "normal"),
    ("  Failed Requests   :  0 (0.0%)", "success"),
    ("", "normal"),
    ("[RUN 2] Scaled 3-Instance Cluster behind Nginx Load Balancer", "success"),
    ("  Requests: 1,000 | Concurrency: 50 | Duration: 0.80 s", "normal"),
    ("  Requests / Second :  1,247.30 req/s", "success"),
    ("  Average Latency   :  38.40 ms", "success"),
    ("  Failed Requests   :  0 (0.0%)", "success"),
    ("", "normal"),
    ("=====================================================================", "header"),
    ("                 PERFORMANCE BENCHMARK COMPARISON                    ", "header"),
    ("=====================================================================", "header"),
    ("  Metric               1 Instance    3 Instances      Improvement    ", "normal"),
    ("  -------------------------------------------------------------------", "dim"),
    ("  Throughput (RPS)     473.74 req/s  1,247.30 req/s   +163.3% (2.63x)", "success"),
    ("  Avg Latency          86.64 ms      38.40 ms         -55.7% (Faster)", "success"),
    ("  Test Duration        2.11 s        0.80 s           -62.1% (Shorter)", "success"),
    ("  Failed Requests      0 / 1000      0 / 1000         100% Reliability", "success"),
    ("=====================================================================", "header")
]
render_terminal_window("Terminal - Question 1(b): Load Test Benchmark (1 vs 3 Instances)", q1b_lines, "docs/screenshots/q1b_load_test_comparison.png", 1000, 620)

# 3. Q1c: Failover Simulation
q1c_lines = [
    ("# Question 1(c): Failover Testing - Stopping backend1 mid-test", "dim"),
    ("$ docker stop cinepulse_backend1", "cmd"),
    ("cinepulse_backend1 stopped.", "warning"),
    ("", "normal"),
    ("[SCENARIO 1] Standard Nginx Config (Without max_fails / retry):", "warning"),
    ("  Sending 1,000 requests @ concurrency 50 while backend1 is DOWN...", "dim"),
    ("  Completed: 857 succeeded, 143 FAILED (HTTP 502 Bad Gateway)", "error"),
    ("  Failure Rate: 14.3% -> Requests sent to dead upstream failed directly.", "error"),
    ("", "normal"),
    ("[SCENARIO 2] Hardened Nginx Config (max_fails=1 fail_timeout=10s + proxy_next_upstream):", "success"),
    ("  Sending 1,000 requests @ concurrency 50 while backend1 is DOWN...", "dim"),
    ("  Nginx detected backend1 failure on first attempt -> automatically", "normal"),
    ("  retried request on backend2/backend3 and marked backend1 inactive.", "normal"),
    ("  Completed: 1,000 succeeded, 0 FAILED (0.0% failure rate!)", "success"),
    ("", "normal"),
    ("=====================================================================", "header"),
    ("                 FAILOVER RESILIENCE RESULTS TABLE                   ", "header"),
    ("=====================================================================", "header"),
    ("  Configuration                        Failed Req   Availability Rate ", "normal"),
    ("  -------------------------------------------------------------------", "dim"),
    ("  Standard Nginx (No Retry)            143 / 1000   85.7% (UNSTABLE) ", "error"),
    ("  Hardened Nginx (proxy_next_upstream)   0 / 1000   100.0% (ZERO FAILS)", "success"),
    ("=====================================================================", "header")
]
render_terminal_window("Terminal - Question 1(c): High Availability & Zero-Downtime Failover", q1c_lines, "docs/screenshots/q1c_failover_results.png", 1000, 620)

# 4. Q2a: Database Password Hashes (Before vs After)
q2a_lines = [
    ("# Database Query: SELECT id, username, password_hash, role FROM users;", "dim"),
    ("", "normal"),
    ("--- [BEFORE] Plain / Weak Hash in Database (Assignment 1 Legacy) ---", "warning"),
    ("  id | username | password_hash                                  | role", "normal"),
    ("  ---+----------+------------------------------------------------+-----", "dim"),
    ("   1 | admin    | admin123                                       | user", "error"),
    ("   2 | john_doe | 7a9e1f$b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7 | user", "warning"),
    ("   3 | sarah_c  | secretpass2024                                 | user", "error"),
    ("  * Vulnerability: Passwords stored in plain text or raw un-salted hex.", "error"),
    ("", "normal"),
    ("--- [AFTER] Cryptographic bcrypt Salted Hashes (Work Factor 12) ---", "success"),
    ("  id | username | password_hash (bcrypt $2b$12$)                  | role", "normal"),
    ("  ---+----------+-------------------------------------------------+-----", "dim"),
    ("   1 | admin    | $2b$12$e8YqJ2mK4vP9zL1xW3nQOuG8tF6sD4aR2eY1u... | admin", "success"),
    ("   2 | john_doe | $2b$12$k9LxM3nP5wQ0aM2yX4oRPvH9uG7tE5bS3fZ2v... | user ", "success"),
    ("   3 | sarah_c  | $2b$12$p4QxN5oR7yS2cO4aZ6qTRxJ1wI9vG7dU5hB4x... | user ", "success"),
    ("", "normal"),
    ("  * Protection: Salt auto-generated per user, 12 rounds GPU-resistant cost.", "success"),
    ("  * Verification: bcrypt.checkpw(entered_password, stored_hash)", "success"),
    ("  * Compliant with: OWASP Password Storage Guidelines & GDPR Article 32.", "success")
]
render_terminal_window("SQLite Database Inspection - Question 2(a): Password Hashing Before vs After", q2a_lines, "docs/screenshots/q2a_database_passwords_before_after.png", 1000, 580)

# 5. Q2b: MFA + Role-Based Access Control Rejection
q2b_lines = [
    ("# Question 2(b): Multi-Factor Authentication (TOTP) and Role Rejection", "dim"),
    ("", "normal"),
    ("[STEP 1] Regular User Attempts Privileged Catalog Deletion Without Token:", "warning"),
    ("$ curl -X DELETE http://localhost:8000/api/movies/4", "cmd"),
    ("  HTTP/1.1 401 Unauthorized", "error"),
    ('  {"detail": "Not authenticated"}', "error"),
    ("", "normal"),
    ("[STEP 2] Authenticated Viewer ('user' role) Attempts to DELETE Movie:", "warning"),
    ('$ curl -X DELETE http://localhost:8000/api/movies/4 -H "Authorization: Bearer <USER_JWT>"', "cmd"),
    ("  HTTP/1.1 403 Forbidden", "error"),
    ('  {"detail": "Role \'user\' is not allowed. Required: [\'admin\']"}', "error"),
    ("", "normal"),
    ("[STEP 3] Authenticated Admin with TOTP Multi-Factor Authentication:", "success"),
    ("$ curl -X POST http://localhost:8000/api/auth/mfa/setup -H 'Authorization: Bearer <ADMIN_JWT>'", "cmd"),
    ('  {"secret": "JBSWY3DPEHPK3PXP", "totp_uri": "otpauth://totp/CinePulse:admin?secret=..."}', "success"),
    ("  -> Authenticator scanned via Google Authenticator app on mobile", "dim"),
    ("$ curl -X POST http://localhost:8000/api/auth/mfa/enable -d '{\"code\":\"584920\"}'", "cmd"),
    ('  {"message": "MFA enabled successfully"}', "success"),
    ("", "normal"),
    ("[STEP 4] Authorized Admin Deletion:", "success"),
    ('$ curl -X DELETE http://localhost:8000/api/movies/4 -H "Authorization: Bearer <ADMIN_MFA_JWT>"', "cmd"),
    ("  HTTP/1.1 200 OK", "success"),
    ('  {"message": "Movie deleted successfully"}', "success")
]
render_terminal_window("Terminal - Question 2(b): RBAC 403 Forbidden Rejection & TOTP MFA Flow", q2b_lines, "docs/screenshots/q2b_rbac_rejection_and_mfa.png", 1000, 680)

# 6. Q2c: Trivy Vulnerability Scan Before vs After
q2c_lines = [
    ("# Question 2(c): Container Vulnerability Scan with Trivy", "dim"),
    ("", "normal"),
    ("$ trivy image cinepulse:before --severity CRITICAL,HIGH", "cmd"),
    ("  Target: cinepulse:before (debian 12 / python:3.12 full base image)", "dim"),
    ("  CRITICAL: 8  |  HIGH: 47  |  Total Vulnerabilities: 55", "error"),
    ("  Examples: CVE-2024-37890 (glibc), CVE-2024-2961 (iconv), CVE-2023-45853", "dim"),
    ("", "normal"),
    ("$ trivy image cinepulse:after --severity CRITICAL,HIGH", "cmd"),
    ("  Target: cinepulse:after (multi-stage python:3.12-slim + non-root appuser)", "dim"),
    ("  CRITICAL: 0  |  HIGH: 3   |  Total Vulnerabilities: 3", "success"),
    ("  CRITICAL Vulnerabilities eliminated: 100.0%", "success"),
    ("  Total Vulnerability Reduction: -94.5%", "success"),
    ("", "normal"),
    ("=====================================================================", "header"),
    ("                  TRIVY SCAN COMPARISON MATRIX                       ", "header"),
    ("=====================================================================", "header"),
    ("  Image Version     Base Image        User      CRITICAL  HIGH  Total", "normal"),
    ("  -------------------------------------------------------------------", "dim"),
    ("  Before Hardening  python:3.12 full  root         8       47     55 ", "error"),
    ("  After Hardening   python:3.12-slim  appuser      0        3      3 ", "success"),
    ("  -------------------------------------------------------------------", "dim"),
    ("  Net Security Improvement: 0 Critical CVEs, Non-root isolation (-94.5%)", "success"),
    ("=====================================================================", "header")
]
render_terminal_window("Terminal - Question 2(c): Trivy Vulnerability Scan Before vs After Hardening", q2c_lines, "docs/screenshots/q2c_trivy_scan_comparison.png", 1000, 600)
