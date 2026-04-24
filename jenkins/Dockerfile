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

# Install kubectl
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ]; then \
        KUBECTL_ARCH="arm64"; \
    else \
        KUBECTL_ARCH="amd64"; \
    fi && \
    curl -fsSL "https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/${KUBECTL_ARCH}/kubectl" \
        -o /usr/local/bin/kubectl && \
    chmod +x /usr/local/bin/kubectl

# Install sonar-scanner CLI
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
