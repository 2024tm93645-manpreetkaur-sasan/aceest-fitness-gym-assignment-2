pipeline {

    agent any

    environment {
        DOCKERHUB_USER  = 'sasanmanpreet91'
        BACKEND_IMAGE   = "${DOCKERHUB_USER}/aceest-fitness-gym-api"
        FRONTEND_IMAGE  = "${DOCKERHUB_USER}/aceest-fitness-gym-ui"
        TAG             = "${env.BUILD_NUMBER}"
        BACKEND_PORT    = '5005'
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

        // ── 6. Acceptance Tests ───────────────────────────────────────
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
            sh "docker network disconnect aceest-net \$(hostname) || true"
            sh "docker network rm aceest-net || true"
            sh "docker logout || true"
        }
    }
}