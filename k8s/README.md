# Kubernetes Deployment

## Prerequisites

### Install Minikube (Mac)
```bash
brew install minikube
brew install kubectl
```

### Start Minikube
```bash
minikube start --driver=docker
```

### Verify
```bash
minikube status
kubectl get nodes
```

---

## First Time Setup (run once per cluster)
```bash
# Create JWT secret in the cluster
kubectl apply -f k8s/rolling-update/secret.yaml
```

---

## Deployment Strategies

### 1. Rolling Update (default pipeline deploy)
```bash
kubectl apply -f k8s/rolling-update/

# Check rollout status
kubectl rollout status deployment/aceest-backend
kubectl rollout status deployment/aceest-frontend

# Rollback if needed
kubectl rollout undo deployment/aceest-backend
kubectl rollout undo deployment/aceest-frontend
```

### 2. Blue-Green
```bash
kubectl apply -f k8s/blue-green/

# Switch traffic to green (new version)
kubectl patch svc aceest-backend-bg-svc \
    -p '{"spec":{"selector":{"slot":"green"}}}'

# Rollback to blue (previous version)
kubectl patch svc aceest-backend-bg-svc \
    -p '{"spec":{"selector":{"slot":"blue"}}}'
```

### 3. Canary (10% traffic to new version)
```bash
kubectl apply -f k8s/canary/

# Check pods (9 stable + 1 canary)
kubectl get pods

# Promote canary to 100%
kubectl scale deployment aceest-backend-canary --replicas=10
kubectl scale deployment aceest-backend-stable --replicas=0

# Rollback
kubectl delete deployment aceest-backend-canary
```

### 4. Shadow
```bash
kubectl apply -f k8s/shadow/

# Production traffic (users see this)
curl http://$(minikube ip):30008/health

# Shadow traffic (v2, responses discarded)
curl http://$(minikube ip):30009/health

# Cleanup
kubectl delete -f k8s/shadow/
```

### 5. A/B Testing
```bash
kubectl apply -f k8s/ab-testing/

# Group A — control (v1)
curl http://$(minikube ip):30010/health

# Group B — variant (v2)
curl http://$(minikube ip):30011/health

# Cleanup
kubectl delete -f k8s/ab-testing/
```

---

## Useful Commands

```bash
# Get all running pods
kubectl get pods

# Get all services and their ports
kubectl get svc

# Get Minikube IP
minikube ip

# Access a service in browser
minikube service aceest-backend-svc

# View pod logs
kubectl logs <pod-name>

# Delete a strategy
kubectl delete -f k8s/rolling-update/

# Stop Minikube
minikube stop
```

---

## Endpoint URL

### Linux / Cloud VM (direct IP works)
```bash
curl http://$(minikube ip):30005/health
echo "Backend URL: http://$(minikube ip):30005"
echo "Frontend URL: http://$(minikube ip):30080"
```

### Mac with Docker driver (NodePort not directly accessible)
```bash
# Get accessible URLs
minikube service aceest-backend-svc --url
minikube service aceest-frontend-svc --url

# Or open directly in browser
minikube service aceest-backend-svc
minikube service aceest-frontend-svc
```

> Note: On Mac with Docker driver, `minikube ip` does not expose NodePorts directly.
> Use `minikube service <name> --url` to get the correct accessible URL.
> This is the URL to submit to sir as proof of running cluster.
