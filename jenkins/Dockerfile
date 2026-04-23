FROM jenkins/jenkins:lts

USER root

# Install Docker CLI, Python, and sonar-scanner dependencies
RUN apt-get update -y && \
    apt-get install -y \
        docker.io \
        python3 \
        python3-pip \
        curl \
        unzip && \
    apt-get clean

# Install sonar-scanner CLI (aarch64/ARM64 for Apple Silicon)
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ]; then \
        SONAR_ZIP="sonar-scanner-cli-6.2.1.4610-linux-aarch64.zip"; \
    else \
        SONAR_ZIP="sonar-scanner-cli-6.2.1.4610-linux-x64.zip"; \
    fi && \
    curl -fsSL "https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/${SONAR_ZIP}" \
        -o /tmp/sonar-scanner.zip && \
    unzip /tmp/sonar-scanner.zip -d /opt && \
    mv /opt/sonar-scanner-6.2.1.4610-linux-* /opt/sonar-scanner && \
    ln -s /opt/sonar-scanner/bin/sonar-scanner /usr/local/bin/sonar-scanner && \
    rm /tmp/sonar-scanner.zip

# Add jenkins user to docker group
RUN usermod -aG docker jenkins

USER jenkins