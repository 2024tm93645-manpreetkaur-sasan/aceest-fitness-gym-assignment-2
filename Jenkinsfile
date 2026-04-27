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

    stage('Checkout') {
        steps {
            checkout scm
            echo "Branch: ${env.GIT_BRANCH} | Build: #${env.BUILD_NUMBER} | Strategy: ${params.STRATEGY}"
        }
    }

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

                    docker logs aceest-backend

                    JENKINS_CONTAINER=$(hostname)
                    docker network connect aceest-net $JENKINS_CONTAINER || true

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
                    pip install -r acceptance-tests/requirements.txt \
                        --break-system-packages -q

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
                junit allowEmptyResults: true,
                      testResults: 'acceptance-test-results.xml'
            }
        }
    }

    stage('Deploy to Minikube') {
        when {
            anyOf {
                branch 'main'
                expression { env.GIT_BRANCH ==~ /.*feature\/k8s-manifests.*/ }
            }
        }
        steps {
            withEnv(["STRATEGY=${params.STRATEGY}"]) {
                sh """
                    export KUBECONFIG=/var/jenkins_home/.kube/config

                    kubectl config use-context minikube
                    kubectl get nodes

                    kubectl apply -f k8s/rolling-update/secret.yaml

                    echo "Deploying strategy: \$STRATEGY"
                    kubectl apply -f k8s/\$STRATEGY/

                    if [ "\$STRATEGY" = "rolling-update" ]; then
                        sed "s|aceest-fitness-gym-api:latest|aceest-fitness-gym-api:${TAG}|g; \
                             s|aceest-fitness-gym-ui:latest|aceest-fitness-gym-ui:${TAG}|g" \
                             k8s/rolling-update/deployment.yaml | kubectl apply -f -

                        kubectl rollout status deployment/aceest-backend  --timeout=120s
                        kubectl rollout status deployment/aceest-frontend --timeout=120s
                    fi

                    kubectl get pods -o wide
                    kubectl get svc
                """
            }
        }
    }
}

post {
    success {
        echo """
        ========================================
         PIPELINE SUCCESS
         Build    : #${env.BUILD_NUMBER}
         Strategy : ${params.STRATEGY}
        ========================================
        """
    }

    failure {
        echo "PIPELINE FAILED - initiating rollback..."
        sh """
            export KUBECONFIG=/var/jenkins_home/.kube/config
            kubectl config use-context minikube 2>/dev/null || true
            kubectl rollout undo deployment/aceest-backend  2>/dev/null || true
            kubectl rollout undo deployment/aceest-frontend 2>/dev/null || true
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
