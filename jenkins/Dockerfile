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

# Install kubectl (architecture-aware)
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ]; then \
        KUBECTL_ARCH="arm64"; \
    else \
        KUBECTL_ARCH="amd64"; \
    fi && \
    curl -fsSL "https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/${KUBECTL_ARCH}/kubectl" \
        -o /usr/local/bin/kubectl && \
    chmod +x /usr/local/bin/kubectl

# Install sonar-scanner CLI (architecture-aware)
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

# Install Google Cloud CLI + GKE auth plugin (architecture-aware)
RUN apt-get update -y && \
    apt-get install -y apt-transport-https ca-certificates gnupg && \
    ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ]; then \
        GCLOUD_ARCH="arm"; \
    else \
        GCLOUD_ARCH="x86_64"; \
    fi && \
    curl -fsSL "https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-${GCLOUD_ARCH}.tar.gz" \
        -o /tmp/gcloud.tar.gz && \
    tar -xzf /tmp/gcloud.tar.gz -C /opt && \
    /opt/google-cloud-sdk/install.sh --quiet && \
    /opt/google-cloud-sdk/bin/gcloud components install gke-gcloud-auth-plugin --quiet && \
    ln -s /opt/google-cloud-sdk/bin/gcloud /usr/local/bin/gcloud && \
    ln -s /opt/google-cloud-sdk/bin/gke-gcloud-auth-plugin /usr/local/bin/gke-gcloud-auth-plugin && \
    rm /tmp/gcloud.tar.gz && \
    apt-get clean

# Add jenkins user to docker group
RUN usermod -aG docker jenkins

USER jenkins