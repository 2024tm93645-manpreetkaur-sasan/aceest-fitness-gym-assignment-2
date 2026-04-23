pipeline {

    agent any

    environment {
        DOCKERHUB_USER  = 'sasanmanpreet91'
        BACKEND_IMAGE   = "${DOCKERHUB_USER}/aceest-fitness-gym-api"
        FRONTEND_IMAGE  = "${DOCKERHUB_USER}/aceest-fitness-gym-ui"
        TAG             = "${env.BUILD_NUMBER}"
    }

    stages {

        // ── 1. Checkout ───────────────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
                echo "Branch: ${env.GIT_BRANCH} | Build: #${env.BUILD_NUMBER}"
            }
        }

        // ── 2. Unit Tests ─────────────────────────────────────────────
        stage('Unit Tests') {
            steps {
                dir('backend') {
                    sh '''
                        pip install -r requirements.txt --break-system-packages -q
                        python3 -m pytest tests/ -v \
                            --junitxml=test-results.xml
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

        // ── 3. Docker Build ───────────────────────────────────────────
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

        // ── 4. Push to Docker Hub ─────────────────────────────────────
        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DH_USER',
                    passwordVariable: 'DH_PASS'
                )]) {
                    sh "echo ${DH_PASS} | docker login -u ${DH_USER} --password-stdin"
                    sh "docker push ${BACKEND_IMAGE}:${TAG}"
                    sh "docker push ${BACKEND_IMAGE}:latest"
                    sh "docker push ${FRONTEND_IMAGE}:${TAG}"
                    sh "docker push ${FRONTEND_IMAGE}:latest"
                }
            }
        }

        // ── 5. Deploy Containers ──────────────────────────────────────
        stage('Deploy Containers') {
            steps {
                sh """
                    # Stop and remove any existing containers
                    docker rm -f aceest-backend aceest-frontend || true

                    # Run backend
                    docker run -d --name aceest-backend \
                        -p 5005:5005 \
                        -e JWT_SECRET_KEY=aceest-test-secret \
                        -e DB_NAME=/tmp/aceest.db \
                        ${BACKEND_IMAGE}:${TAG}

                    # Run frontend linked to backend
                    docker run -d --name aceest-frontend \
                        -p 3000:80 \
                        --link aceest-backend:backend \
                        ${FRONTEND_IMAGE}:${TAG}

                    # Wait for containers to be ready
                    sleep 15

                    # Quick sanity check
                    curl --fail http://localhost:5005/health
                    echo "Containers are up"
                """
            }
        }

        // ── 6. Acceptance Tests ───────────────────────────────────────
        stage('Acceptance Tests') {
            steps {
                sh '''
                    pip install -r acceptance-tests/requirements.txt \
                        --break-system-packages -q
                    APP_URL=http://localhost:5005 \
                    ADMIN_USERNAME=admin \
                    ADMIN_PASSWORD=admin123 \
                    python3 -m pytest acceptance-tests/ -v \
                        --junitxml=acceptance-test-results.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true,
                          testResults: 'acceptance-test-results.xml'
                }
            }
        }
    }

    // ── Post Actions ──────────────────────────────────────────────────
    post {
        success {
            echo """
            ========================================
             PIPELINE SUCCESS
             Build   : #${env.BUILD_NUMBER}
             Backend : ${BACKEND_IMAGE}:${TAG}
             Frontend: ${FRONTEND_IMAGE}:${TAG}
            ========================================
            """
        }
        failure {
            echo "PIPELINE FAILED — check logs above"
        }
        always {
            sh "docker rm -f aceest-backend aceest-frontend || true"
            sh "docker logout || true"
        }
    }
}