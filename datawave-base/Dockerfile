ARG BUILDER_IMAGE_NAME=registry.access.redhat.com/ubi8/ubi
ARG BUILDER_IMAGE_TAG=8.7
ARG CORRETTO_VERSION=11.0.19.7

FROM ${BUILDER_IMAGE_NAME}:${BUILDER_IMAGE_TAG}

ARG CORRETTO_VERSION

# add amazon yum repo
RUN rpm --import https://yum.corretto.aws/corretto.key && \
    curl -L -o /etc/yum.repos.d/corretto.repo https://yum.corretto.aws/corretto.repo  && \
    rpm -ivh https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm && \
    yum install -y java-11-amazon-corretto-devel-${CORRETTO_VERSION} \
    gcc-c++ \
    make \
    ncurses \
    wget \
    pdsh \
    genders \
    pdsh-mod-genders \
    hostname \
	&& yum clean all && rm -Rf /var/cache/yum

ENV JAVA_HOME /usr/lib/jvm/java

