# Jenkins Setup

## Start
```bash
cd jenkins/
docker compose up -d
docker compose exec -u root jenkins chmod 666 /var/run/docker.sock
```

## Unlock
```bash
docker compose exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```
Open http://localhost:8080 and paste the password.

## Credentials to add
Jenkins → Manage Jenkins → Credentials → Global → Add Credentials

| ID | Username | Password |
|----|----------|----------|
| `dockerhub-creds` | `sasanmanpreet91` | Docker Hub access token |
| `github-pat` | your GitHub username | GitHub PAT |

## Pipeline Job
1. New Item → `aceest-fitness-gym-assignment2` → Pipeline → OK
2. Build Triggers → Poll SCM → `H/5 * * * *`
3. Pipeline → Pipeline script from SCM → Git
4. Repository URL: your GitHub repo URL
5. Credentials: `github-pat`
6. Branch: `*/feature/*`
7. Script Path: `Jenkinsfile`
8. Save

## Stop
```bash
docker compose down
```