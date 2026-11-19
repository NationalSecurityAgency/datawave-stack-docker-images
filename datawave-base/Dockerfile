# syntax=docker/dockerfile:1
ARG BUILDER_IMAGE_NAME=registry.access.redhat.com/ubi8/ubi
ARG BUILDER_IMAGE_TAG=8.10

FROM ${BUILDER_IMAGE_NAME}:${BUILDER_IMAGE_TAG}

ARG JAVA_VERSION=11

# add amazon yum repo
RUN case "${JAVA_VERSION}" in 11|17) ;; *) exit 1 ;; esac && \
    rpm --import https://yum.corretto.aws/corretto.key && \
    curl -fL -o /etc/yum.repos.d/corretto.repo https://yum.corretto.aws/corretto.repo && \
    rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm && \
    yum update -y  && \
    yum install -y java-${JAVA_VERSION}-amazon-corretto-devel \
    gcc-c++ \
    make \
    ncurses \
    wget \
    pdsh \
    genders \
    pdsh-mod-genders \
    hostname \
    && ln -s "$(dirname "$(dirname "$(readlink -f /usr/bin/javac)")")" /opt/java \
    && yum clean all && rm -rf /var/cache/yum /var/cache/dnf \
    && rpm -qa | sort > /rpm-manifest.txt

ENV JAVA_HOME=/opt/java
ENV PATH=${JAVA_HOME}/bin:${PATH}

