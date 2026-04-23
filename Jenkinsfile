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

        // ── 5. Deploy Containers ──────────────────────────────────────
        stage('Deploy Containers') {
            steps {
                sh '''
                    # Stop any existing containers
                    docker rm -f aceest-backend aceest-frontend || true
                    docker network rm aceest-net || true
                    docker network create aceest-net

                    # Run backend on shared network
                    docker run -d --name aceest-backend \
                        --network aceest-net \
                        -e JWT_SECRET_KEY=aceest-test-secret \
                        -e DB_NAME=/tmp/aceest.db \
                        ${BACKEND_IMAGE}:${TAG}

                    # Run frontend on same network
                    docker run -d --name aceest-frontend \
                        --network aceest-net \
                        ${FRONTEND_IMAGE}:${TAG}

                    # Wait for containers to start
                    sleep 15

                    # Print logs to confirm startup
                    echo "=== Backend container logs ==="
                    docker logs aceest-backend
                    echo "=============================="

                    # Connect Jenkins container to aceest-net so it can reach backend
                    JENKINS_CONTAINER=$(hostname)
                    docker network connect aceest-net $JENKINS_CONTAINER || true

                    # Hit backend by container name (DNS resolves on shared network)
                    curl --fail http://aceest-backend:5005/health
                    echo "Containers are up"

                    # Save backend hostname for acceptance tests
                    echo "aceest-backend" > /tmp/backend_host.txt
                '''
            }
        }

        // ── 6. Acceptance Tests ───────────────────────────────────────
        stage('Acceptance Tests') {
            steps {
                sh '''
                    pip install -r acceptance-tests/requirements.txt \
                        --break-system-packages -q

                    BACKEND_HOST=$(cat /tmp/backend_host.txt)
                    echo "Running acceptance tests against http://${BACKEND_HOST}:5005"

                    APP_URL=http://${BACKEND_HOST}:5005 \
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
            sh "docker network rm aceest-net || true"
            sh "docker logout || true"
        }
    }
}