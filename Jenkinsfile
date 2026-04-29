pipeline {

    agent any

    environment {
        DOCKERHUB_USER  = 'sasanmanpreet91'
        BACKEND_IMAGE   = "${DOCKERHUB_USER}/aceest-fitness-gym-api"
        FRONTEND_IMAGE  = "${DOCKERHUB_USER}/aceest-fitness-gym-ui"
        TAG             = "${env.BUILD_NUMBER}"
        BACKEND_PORT    = '5005'
        SONAR_PROJECT   = 'aceest-fitness-gym'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                echo "Branch: ${env.GIT_BRANCH} | Build: #${env.BUILD_NUMBER}"
            }
        }

        stage('Unit Tests') {
            steps {
                dir('backend') {
                    sh '''
                        set -e
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
                    junit allowEmptyResults: true, testResults: 'backend/test-results.xml'
                }
            }
        }

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

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Docker Login') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DH_USER',
                    passwordVariable: 'DH_PASS'
                )]) {
                    sh """
                        echo \$DH_PASS | docker login -u \$DH_USER --password-stdin
                        docker buildx create --use --name multi-builder \
                            --driver docker-container \
                            --platform linux/amd64,linux/arm64 2>/dev/null || \
                        docker buildx use multi-builder
                    """
                }
            }
        }

        stage('Docker Build') {
            parallel {
                stage('Backend Build') {
                    steps {
                        sh """
                            docker buildx build \
                                --platform linux/amd64,linux/arm64 \
                                -t ${BACKEND_IMAGE}:${TAG} \
                                -t ${BACKEND_IMAGE}:latest \
                                --push ./backend
                        """
                    }
                }

                stage('Frontend Build') {
                    steps {
                        sh """
                            docker buildx build \
                                --platform linux/amd64,linux/arm64 \
                                -t ${FRONTEND_IMAGE}:${TAG} \
                                -t ${FRONTEND_IMAGE}:latest \
                                --push ./frontend
                        """
                    }
                }
            }
        }

        stage('Verify Push') {
            steps {
                sh """
                    docker buildx imagetools inspect ${BACKEND_IMAGE}:${TAG} | grep Platform
                    docker buildx imagetools inspect ${FRONTEND_IMAGE}:${TAG} | grep Platform
                """
            }
        }

        stage('Deploy Containers') {
            steps {
                withCredentials([string(credentialsId: 'jwt-secret', variable: 'JWT_SECRET_KEY')]) {
                    sh '''
                        set -e
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
                        curl --fail http://aceest-backend:${BACKEND_PORT}/health

                        echo "aceest-backend" > /tmp/backend_host.txt
                    '''
                }
            }
        }

        stage('Acceptance Tests') {
            steps {
                withCredentials([
                    string(credentialsId: 'app-admin-username', variable: 'ADMIN_USERNAME'),
                    string(credentialsId: 'app-admin-password', variable: 'ADMIN_PASSWORD')
                ]) {
                    sh '''
                        pip install -r acceptance-tests/requirements.txt --break-system-packages -q
                        BACKEND_HOST=$(cat /tmp/backend_host.txt)

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
                    junit allowEmptyResults: true, testResults: 'acceptance-test-results.xml'
                }
            }
        }

        stage('GKE Setup & Deploy') {
            when {
                anyOf {
                    branch 'main'
                    expression { env.GIT_BRANCH ==~ /.*feature\/k8s-manifests.*/ }
                }
            }
            steps {
                withCredentials([
                    file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY'),
                    usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')
                ]) {
                    sh '''
                        set -e
                        gcloud auth activate-service-account --key-file=$GCP_KEY
                        gcloud config set project aceest-devops
                        gcloud container clusters get-credentials aceest-cluster --zone asia-south1-a

                        for NS in rolling blue-green canary shadow ab-testing; do
                            kubectl create namespace $NS --dry-run=client -o yaml | kubectl apply -f -

                            kubectl create secret docker-registry dockerhub-secret \
                                --docker-username=$DH_USER \
                                --docker-password=$DH_PASS \
                                --docker-server=https://index.docker.io/v1/ \
                                --namespace=$NS \
                                --dry-run=client -o yaml | kubectl apply -f -
                        done

                        kubectl apply -f k8s/rolling-update/secret.yaml
                    '''
                }
            }
        }

        stage('Deploy All Strategies') {
            when {
                anyOf {
                    branch 'main'
                    expression { env.GIT_BRANCH ==~ /.*feature\/k8s-manifests.*/ }
                }
            }
            parallel {

                stage('Rolling') {
                    steps {
                        sh """
                            sed 's|:latest|:${TAG}|g' k8s/rolling-update/deployment.yaml | kubectl apply -n rolling -f -
                            kubectl apply -n rolling -f k8s/rolling-update/service.yaml
                            kubectl rollout status deployment/aceest-backend -n rolling
                        """
                    }
                }

                stage('Blue-Green') {
                    steps {
                        sh "kubectl apply -n blue-green -f k8s/blue-green/"
                    }
                }

                stage('Canary') {
                    steps {
                        sh "kubectl apply -n canary -f k8s/canary/"
                    }
                }

                stage('Shadow') {
                    steps {
                        sh "kubectl apply -n shadow -f k8s/shadow/"
                    }
                }

                stage('AB Testing') {
                    steps {
                        sh "kubectl apply -n ab-testing -f k8s/ab-testing/"
                    }
                }
            }
        }

        stage('Public URLs') {
            when {
                anyOf {
                    branch 'main'
                    expression { env.GIT_BRANCH ==~ /.*feature\/k8s-manifests.*/ }
                }
            }
            steps {
                sh '''
                    sleep 60
                    for NS in rolling blue-green canary shadow ab-testing; do
                        echo "=== $NS ==="
                        kubectl get svc -n $NS
                    done
                '''
            }
        }
    }

    post {
        success {
            echo """
            ========================================
             PIPELINE SUCCESS
             Build   : #${env.BUILD_NUMBER}
             Backend : ${BACKEND_IMAGE}:${TAG}
             Frontend: ${FRONTEND_IMAGE}:${TAG}
             Cluster : aceest-cluster (GKE)
            ========================================
            """
        }

        failure {
            sh '''
                gcloud container clusters get-credentials aceest-cluster \
                    --zone asia-south1-a --project aceest-devops || true
                kubectl rollout undo deployment/aceest-backend -n rolling || true
                kubectl rollout undo deployment/aceest-frontend -n rolling || true
            '''
        }

        always {
            sh '''
                docker rm -f aceest-backend aceest-frontend || true
                docker network rm aceest-net || true
                docker logout || true
            '''
        }
    }
}