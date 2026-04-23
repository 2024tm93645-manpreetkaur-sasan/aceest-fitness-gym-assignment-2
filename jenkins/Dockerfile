FROM jenkins/jenkins:lts

USER root

# Install Docker CLI so Jenkins can build images
RUN apt-get update -y && \
    apt-get install -y \
        docker.io \
        python3 \
        python3-pip && \
    apt-get clean

# Add jenkins user to docker group
RUN usermod -aG docker jenkins

USER jenkins