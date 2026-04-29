# ACEest Fitness & Gym — Assignment 2

Flask + React fitness management app with a fully automated Jenkins CI/CD pipeline deployed to Google Kubernetes Engine (GKE). Also validated on Minikube locally (Mac) and on AWS EC2.

## Stack

| Layer | Tool |
|---|---|
| Backend | Flask (Python 3.11), JWT auth, SQLite |
| Frontend | React, nginx (envsubst for backend proxy) |
| CI/CD | Jenkins (self-hosted via Docker Compose) |
| Code Quality | SonarQube 25.1 |
| Containers | Docker buildx — multi-platform amd64 + arm64 |
| Registry | Docker Hub — sasanmanpreet91 |
| Orchestration (primary) | GKE — aceest-cluster, asia-south1-a |
| Orchestration (local) | Minikube on Mac (local dev validation) |
| Orchestration (EC2) | Minikube on AWS EC2 t3.small, eu-north-1 (16.16.171.103) |

## Pipeline (12 Stages)

1. Checkout
2. Unit Tests — 58 Pytest tests
3. SonarQube Analysis
4. Quality Gate
5. Docker Login (buildx multi-platform setup)
6. Docker Build — parallel backend + frontend (amd64 + arm64)
7. Verify Push
8. Deploy Containers (local health check)
9. Acceptance Tests — 24 end-to-end API tests
10. GKE Auth
11. Deploy All Strategies (parallel)
12. Public URLs

## Branch Strategy

```
main
├── develop
│   ├── feature/jenkins-pipeline    # Jenkins setup, pipeline stages, SonarQube integration
│   └── feature/k8s-manifests       # Kubernetes manifests, GKE deployment, all 5 strategies
```

| Branch | Purpose |
|---|---|
| `main` | Stable, submission-ready code. Final merges and version tags here. |
| `develop` | Integration branch. Features merged here before going to main. |
| `feature/jenkins-pipeline` | Jenkins Dockerfile, docker-compose, Jenkinsfile pipeline stages 1-9 |
| `feature/k8s-manifests` | All K8s manifests, GKE deploy stages 10-12, multi-platform Docker builds |

All commits follow the convention `ACEEST-A2|<type>: <description>` — e.g. `ACEEST-A2|feat: multi-platform builds (amd64+arm64)`.


## Deployment Strategies

All 5 strategies deploy simultaneously to separate namespaces on the same GKE cluster. Each strategy was first validated on Minikube (Mac locally and EC2) before deploying to GKE.

| Strategy | Namespace | Stable (:42 Ocean Blue) | New (:43 Forest Green) |
|---|---|---|---|
| Rolling Update | rolling | — | :49 (latest) |
| Blue-Green | blue-green | blue slot | green slot |
| Canary | canary | 2 replicas | 1 replica |
| Shadow | shadow | serves real users | mirrored traffic (discarded) |
| A/B Testing | ab-testing | Group A | Group B |

## Running Locally

```bash
# Start Jenkins + SonarQube
cd jenkins/
docker compose up -d
docker compose exec -u root jenkins chmod 666 /var/run/docker.sock

# Run backend directly
cd backend/
pip install -r requirements.txt
python app.py

# Run frontend
cd frontend/
npm install && npm start
```

## Minikube (Local — Mac)

```bash
minikube start

# Rolling Update
kubectl apply -f k8s/rolling-update/
kubectl rollout status deployment/aceest-backend -n rolling

# Blue-Green
kubectl apply -f k8s/blue-green/
# Switch traffic: kubectl patch svc aceest-backend-bg-svc -n blue-green \
#   -p '{"spec":{"selector":{"slot":"green"}}}'

# Canary
kubectl apply -f k8s/canary/
# Promote: kubectl scale deployment aceest-backend-canary -n canary --replicas=3
# Abort:   kubectl delete deployment aceest-backend-canary -n canary

# Shadow
kubectl apply -f k8s/shadow/
# Stable serves users, shadow receives mirrored traffic silently

# A/B Testing
kubectl apply -f k8s/ab-testing/
# Group A: aceest-backend-version-a-svc
# Group B: aceest-backend-version-b-svc

# Access frontend
minikube service aceest-frontend-svc -n rolling
kubectl get svc --all-namespaces
```

## Minikube (EC2 — AWS t3.small, eu-north-1)

```bash
# SSH into EC2
ssh -i key.pem ec2-user@16.16.171.103

# Start Minikube
minikube start --driver=docker

# Rolling Update
kubectl apply -f k8s/rolling-update/
kubectl rollout status deployment/aceest-backend -n rolling

# Blue-Green
kubectl apply -f k8s/blue-green/
kubectl apply -f k8s/blue-green/service.yaml
# Switch: kubectl patch svc aceest-backend-bg-svc -n blue-green \
#   -p '{"spec":{"selector":{"slot":"green"}}}'

# Canary
kubectl apply -f k8s/canary/
kubectl get pods -n canary  # 2 stable + 1 canary

# Shadow
kubectl apply -f k8s/shadow/
kubectl get svc -n shadow   # stable-svc and shadow-svc

# A/B Testing
kubectl apply -f k8s/ab-testing/
kubectl get svc -n ab-testing  # version-a-svc and version-b-svc

kubectl get pods --all-namespaces
kubectl get svc --all-namespaces
```

## Testing

```bash
# Unit tests
cd backend/
pytest tests/ -v --cov=.

# Acceptance tests (requires running backend)
APP_URL=http://localhost:5005 pytest acceptance-tests/ -v
```

## Docker Images

```
sasanmanpreet91/aceest-fitness-gym-api   :42 :43 :44 :latest
sasanmanpreet91/aceest-fitness-gym-ui    :42 :43 :44 :latest
```

All images are multi-platform (linux/amd64 + linux/arm64).

## GKE Public Endpoints (Build #48)

| Strategy | URL |
|---|---|
| Rolling — backend | http://34.93.3.230 |
| Rolling — frontend | http://34.93.181.162 |
| Blue-Green (active) | http://34.180.63.229 |
| Canary (:43) | http://34.14.166.100 |
| Shadow stable (:42) | http://34.93.209.188 |
| Shadow mirror (:43) | http://34.93.61.221 |
| A/B Group A (:42) | http://34.93.225.70 |
| A/B Group B (:43) | http://34.180.49.148 |