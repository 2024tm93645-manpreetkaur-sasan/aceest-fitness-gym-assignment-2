# Jenkins + SonarQube Setup

## Start

```bash
cd jenkins/

# First time or after Dockerfile changes:
docker compose up -d --build

# Subsequent starts:
docker compose up -d

docker compose exec -u root jenkins chmod 666 /var/run/docker.sock
```

## Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Jenkins | http://localhost:8080 | see unlock below |
| SonarQube | http://localhost:9000 | admin / admin |

## Unlock Jenkins

```bash
docker compose exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

## SonarQube First-Time Setup
1. Open http://localhost:9000 → login with `admin` / `admin`
2. Change password when prompted (set a new one)
3. Top right avatar → **My Account** → **Security** tab
4. Under **Generate Tokens**:
    - Name: `jenkins-sonar`
    - Type: `Global Analysis Token`
    - Expiry: `No expiration`
    - Click **Generate**
    - Copy the token immediately (shown only once)
5. Add to Jenkins credentials:
    - Manage Jenkins → Credentials → Global → Add Credentials
    - Kind: `Secret text`
    - ID: `sonar-token`
    - Value: paste the token

## Configure SonarQube in Jenkins
1. Manage Jenkins → System → SonarQube servers → Add
    - Name: `SonarQube`
    - URL: `http://sonarqube:9000`
    - Token: select `sonar-token` credential
2. Manage Jenkins → Tools → SonarQube Scanner → Add
    - Name: `SonarQube Scanner`
    - Install automatically: ✅

## Jenkins Credentials needed

| ID | Kind | Value |
|----|------|-------|
| `dockerhub-creds` | Username + password | Docker Hub |
| `github-pat` | Username + password | GitHub PAT |
| `jwt-secret` | Secret text | JWT key |
| `app-admin-username` | Secret text | admin |
| `app-admin-password` | Secret text | admin123 |
| `sonar-token` | Secret text | SonarQube token |

## Pipeline Job Setup
1. New Item → `aceest-fitness-gym` → Pipeline → OK
2. Build Triggers → choose one of the options below
3. Pipeline → Pipeline script from SCM → Git
4. Repository URL: your GitHub repo URL
5. Credentials: `github-pat`
6. Branch: `*/develop`
7. Script Path: `Jenkinsfile`
8. Save

## Build Trigger Options

### Option A — Poll SCM (simpler, no extra setup)
- Tick `Poll SCM`
- Schedule: `H/5 * * * *`
- Jenkins checks GitHub every 5 minutes for new commits

### Option B — GitHub Webhook via ngrok (instant trigger on push)

**Step 1 — Start ngrok:**
```bash
brew install ngrok   # if not installed
ngrok http 8080
```
Copy the forwarding URL e.g. `https://abc123.ngrok-free.app`

**Step 2 — Add webhook in GitHub:**
- Repo → Settings → Webhooks → Add webhook
- Payload URL: `https://abc123.ngrok-free.app/github-webhook/`
- Content type: `application/json`
- Events: `Just the push event`
- Save → verify green tick ✅

**Step 3 — Configure Jenkins job:**
- Build Triggers → tick `GitHub hook trigger for GITScm polling`

> **Note:** Free ngrok URL changes every session. Update the GitHub webhook URL each time you restart ngrok.

## Stop

```bash
docker compose down
```