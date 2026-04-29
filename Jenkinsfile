pipeline {

    agent any

    parameters {
        choice(
            name: 'STRATEGY',
            choices: ['rolling-update', 'blue-green', 'canary', 'shadow', 'ab-testing'],
            description: 'Select Kubernetes deployment strategy'
        )
    }

    environment {
        DOCKERHUB_USER  = 'sasanmanpreet91'
        BACKEND_IMAGE   = "${DOCKERHUB_USER}/aceest-fitness-gym-api"
        FRONTEND_IMAGE  = "${DOCKERHUB_USER}/aceest-fitness-gym-ui"
        TAG             = "${env.BUILD_NUMBER}"
        BACKEND_PORT    = '5005'
        SONAR_PROJECT   = 'aceest-fitness-gym'
    }

    stages {

        // ── 1. Checkout ───────────────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
                echo "Branch: ${env.GIT_BRANCH} | Build: #${env.BUILD_NUMBER} | Strategy: ${params.STRATEGY}"
            }
        }

        // ── 2. Unit Tests ─────────────────────────────────────────────
        stage('Unit Tests') {
            steps {
                dir('backend') {
                    sh '''
                        pip install -r requirements.txt pytest-cov coverage --break-system-packages -q
                        python3 -m pytest tests/ -v \
                            --junitxml=test-results.xml \
                            --cov=. \
                            --cov-report=xml:coverage.xml
                    '''
                }
            }
            post {
                always {
                    junit allowEmptyResults: true,
                          testResults: 'backend/test-results.xml'
                }
            }
        }

        // ── 3. SonarQube Analysis ─────────────────────────────────────
        stage('SonarQube Analysis') {
            steps {
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                    withSonarQubeEnv('SonarQube') {
                        sh """
                            sonar-scanner \
                                -Dsonar.projectKey=${SONAR_PROJECT} \
                                -Dsonar.projectName="ACEest Fitness and Gym" \
                                -Dsonar.sources=backend \
                                -Dsonar.exclusions=backend/tests/**,backend/utils/pdf.py \
                                -Dsonar.python.coverage.reportPaths=backend/coverage.xml \
                                -Dsonar.python.version=3.11 \
                                -Dsonar.host.url=http://sonarqube:9000 \
                                -Dsonar.token=$SONAR_TOKEN
                        """
                    }
                }
            }
        }

        // ── 4. Quality Gate ───────────────────────────────────────────
        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        // ── 5. Docker Build ───────────────────────────────────────────
        stage('Docker Build') {
            parallel {
                stage('[Backend] Build') {
                    steps {
                        sh "docker build -t ${BACKEND_IMAGE}:${TAG} ./backend"
                        sh "docker tag ${BACKEND_IMAGE}:${TAG} ${BACKEND_IMAGE}:latest"
                    }
                }
                stage('[Frontend] Build') {
                    steps {
                        sh "docker build -t ${FRONTEND_IMAGE}:${TAG} ./frontend"
                        sh "docker tag ${FRONTEND_IMAGE}:${TAG} ${FRONTEND_IMAGE}:latest"
                    }
                }
            }
        }

        // ── 6. Push to Docker Hub ─────────────────────────────────────
        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DH_USER',
                    passwordVariable: 'DH_PASS'
                )]) {
                    sh '''
                        echo $DH_PASS | docker login -u $DH_USER --password-stdin
                        docker push ${BACKEND_IMAGE}:${TAG}
                        docker push ${BACKEND_IMAGE}:latest
                        docker push ${FRONTEND_IMAGE}:${TAG}
                        docker push ${FRONTEND_IMAGE}:latest
                    '''
                }
            }
        }

        // ── 7. Deploy Containers ──────────────────────────────────────
        stage('Deploy Containers') {
            steps {
                withCredentials([
                    string(credentialsId: 'jwt-secret', variable: 'JWT_SECRET_KEY')
                ]) {
                    sh '''
                        docker rm -f aceest-backend aceest-frontend || true
                        docker network rm aceest-net || true
                        docker network create aceest-net

                        docker run -d --name aceest-backend \
                            --network aceest-net \
                            -e JWT_SECRET_KEY=$JWT_SECRET_KEY \
                            -e DB_NAME=/tmp/aceest.db \
                            ${BACKEND_IMAGE}:${TAG}

                        docker run -d --name aceest-frontend \
                            --network aceest-net \
                            ${FRONTEND_IMAGE}:${TAG}

                        sleep 15

                        echo "=== Backend container logs ==="
                        docker logs aceest-backend
                        echo "=============================="

                        JENKINS_CONTAINER=$(hostname)
                        docker network connect aceest-net $JENKINS_CONTAINER || true

                        curl --fail http://aceest-backend:${BACKEND_PORT}/health
                        echo "Containers are up"

                        echo "aceest-backend" > /tmp/backend_host.txt
                    '''
                }
            }
        }

        // ── 8. Acceptance Tests ───────────────────────────────────────
        stage('Acceptance Tests') {
            steps {
                withCredentials([
                    string(credentialsId: 'app-admin-username', variable: 'ADMIN_USERNAME'),
                    string(credentialsId: 'app-admin-password', variable: 'ADMIN_PASSWORD')
                ]) {
                    sh '''
                        pip install -r acceptance-tests/requirements.txt \
                            --break-system-packages -q

                        BACKEND_HOST=$(cat /tmp/backend_host.txt)
                        echo "Running acceptance tests against http://${BACKEND_HOST}:${BACKEND_PORT}"

                        APP_URL=http://${BACKEND_HOST}:${BACKEND_PORT} \
                        ADMIN_USERNAME=$ADMIN_USERNAME \
                        ADMIN_PASSWORD=$ADMIN_PASSWORD \
                        python3 -m pytest acceptance-tests/ -v \
                            --junitxml=acceptance-test-results.xml
                    '''
                }
            }
            post {
                always {
                    junit allowEmptyResults: true,
                          testResults: 'acceptance-test-results.xml'
                }
            }
        }

        // ── 9. GKE Auth + Setup ───────────────────────────────────────
        stage('GKE Auth') {
            when {
                anyOf {
                    branch 'main'
                    expression { env.GIT_BRANCH ==~ /.*feature\/k8s-manifests.*/ }
                }
            }
            steps {
                withCredentials([file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY')]) {
                    sh """
                        gcloud auth activate-service-account --key-file=\$GCP_KEY
                        gcloud config set project aceest-devops
                        gcloud container clusters get-credentials aceest-cluster \
                            --zone asia-south1-a --project aceest-devops

                        # Create all namespaces
                        kubectl apply -f k8s-gke/rolling-update/namespace.yaml
                        kubectl apply -f k8s-gke/blue-green/namespace.yaml
                        kubectl apply -f k8s-gke/canary/namespace.yaml
                        kubectl apply -f k8s-gke/shadow/namespace.yaml
                        kubectl apply -f k8s-gke/ab-testing/namespace.yaml

                        # Create Docker Hub pull secret in all namespaces
                        for NS in rolling blue-green canary shadow ab-testing; do
                            kubectl create secret docker-registry dockerhub-secret \
                                --docker-username=sasanmanpreet91 \
                                --docker-password=dckr_pat_lRmJF1jFfKuq5X88k6d9brvBRog \
                                --docker-server=https://index.docker.io/v1/ \
                                --namespace=\$NS \
                                --dry-run=client -o yaml | kubectl apply -f -
                        done

                        # Create JWT secret in rolling namespace
                        kubectl apply -f k8s-gke/rolling-update/secret.yaml

                        echo "GKE setup complete"
                        kubectl get nodes
                    """
                }
            }
        }

        // ── 10. Deploy All Strategies in Parallel ─────────────────────
        stage('Deploy All Strategies') {
            when {
                anyOf {
                    branch 'main'
                    expression { env.GIT_BRANCH ==~ /.*feature\/k8s-manifests.*/ }
                }
            }
            parallel {

                stage('Rolling Update') {
                    steps {
                        sh """
                            sed 's|aceest-fitness-gym-api:latest|aceest-fitness-gym-api:${TAG}|g; s|aceest-fitness-gym-ui:latest|aceest-fitness-gym-ui:${TAG}|g' \
                                k8s-gke/rolling-update/deployment.yaml | kubectl apply -n rolling -f -
                            kubectl apply -n rolling -f k8s-gke/rolling-update/service.yaml
                            kubectl rollout status deployment/aceest-backend -n rolling --timeout=180s
                            kubectl rollout status deployment/aceest-frontend -n rolling --timeout=180s
                            echo "Rolling Update deployed"
                        """
                    }
                }

                stage('Blue-Green') {
                    steps {
                        sh """
                            kubectl apply -n blue-green -f k8s-gke/blue-green/deployment.yaml
                            kubectl apply -n blue-green -f k8s-gke/blue-green/service.yaml
                            kubectl rollout status deployment/aceest-backend-blue -n blue-green --timeout=180s
                            echo "Blue-Green deployed"
                        """
                    }
                }

                stage('Canary') {
                    steps {
                        sh """
                            kubectl apply -n canary -f k8s-gke/canary/deployment.yaml
                            kubectl apply -n canary -f k8s-gke/canary/service.yaml
                            kubectl rollout status deployment/aceest-backend-stable -n canary --timeout=180s
                            echo "Canary deployed"
                        """
                    }
                }

                stage('Shadow') {
                    steps {
                        sh """
                            kubectl apply -n shadow -f k8s-gke/shadow/deployment.yaml
                            kubectl apply -n shadow -f k8s-gke/shadow/service.yaml
                            kubectl rollout status deployment/aceest-backend-stable-shadow -n shadow --timeout=180s
                            echo "Shadow deployed"
                        """
                    }
                }

                stage('AB Testing') {
                    steps {
                        sh """
                            kubectl apply -n ab-testing -f k8s-gke/ab-testing/deployment.yaml
                            kubectl apply -n ab-testing -f k8s-gke/ab-testing/service.yaml
                            kubectl rollout status deployment/aceest-backend-version-a -n ab-testing --timeout=180s
                            echo "AB Testing deployed"
                        """
                    }
                }

            }
        }

        // ── 11. Print All Public URLs ──────────────────────────────────
        stage('Public URLs') {
            when {
                anyOf {
                    branch 'main'
                    expression { env.GIT_BRANCH ==~ /.*feature\/k8s-manifests.*/ }
                }
            }
            steps {
                sh """
                    echo "Waiting 60s for LoadBalancer IPs to be assigned..."
                    sleep 60

                    echo ""
                    echo "================================================================"
                    echo " ALL STRATEGIES DEPLOYED - ACEest Fitness & Gym on GKE"
                    echo " Build #${TAG} | Cluster: aceest-cluster (asia-south1-a)"
                    echo "================================================================"

                    echo ""
                    echo "--- Rolling Update (namespace: rolling) ---"
                    kubectl get svc -n rolling

                    echo ""
                    echo "--- Blue-Green (namespace: blue-green) ---"
                    kubectl get svc -n blue-green

                    echo ""
                    echo "--- Canary (namespace: canary) ---"
                    kubectl get svc -n canary

                    echo ""
                    echo "--- Shadow (namespace: shadow) ---"
                    kubectl get svc -n shadow

                    echo ""
                    echo "--- AB Testing (namespace: ab-testing) ---"
                    kubectl get svc -n ab-testing

                    echo ""
                    echo "================================================================"
                    echo " NOTES:"
                    echo " - All services use LoadBalancer type"
                    echo " - Access each URL at http://<EXTERNAL-IP>/health"
                    echo " - Blue-Green: patch svc selector to switch blue/green"
                    echo " - Canary: scale canary replicas to promote"
                    echo "================================================================"
                """
            }
        }
    }

    // ── Post Actions ──────────────────────────────────────────────────
    post {
        success {
            echo """
            ========================================
             PIPELINE SUCCESS
             Build    : #${env.BUILD_NUMBER}
             Strategy : ${params.STRATEGY}
             Backend  : ${BACKEND_IMAGE}:${TAG}
             Frontend : ${FRONTEND_IMAGE}:${TAG}
             Cluster  : aceest-cluster (GKE)
            ========================================
            """
        }
        failure {
            echo "PIPELINE FAILED - initiating rollback on rolling-update namespace..."
            sh """
                gcloud container clusters get-credentials aceest-cluster \
                    --zone asia-south1-a --project aceest-devops 2>/dev/null || true
                kubectl rollout undo deployment/aceest-backend  -n rolling 2>/dev/null || true
                kubectl rollout undo deployment/aceest-frontend -n rolling 2>/dev/null || true
                echo "Rollback complete"
            """
        }
        always {
            sh "docker rm -f aceest-backend aceest-frontend || true"
            sh "docker network disconnect aceest-net \$(hostname) || true"
            sh "docker network rm aceest-net || true"
            sh "docker logout || true"
        }
    }
}