ARG REGISTRY="ghcr.io/nationalsecurityagency/datawave"
ARG BUILDER_IMAGE_NAME=${REGISTRY}/datawave-stack-hadoop

ARG BUILDER_IMAGE_TAG=3.4.2

ARG BASE_IMAGE_NAME=${REGISTRY}/datawave-stack-hadoop
ARG BASE_IMAGE_TAG=3.4.2

ARG ACCUMULO_VERSION=2.1.4
ARG ZOOKEEPER_VERSION=3.8.5

FROM ${BUILDER_IMAGE_NAME}:${BUILDER_IMAGE_TAG} AS builder

ARG ACCUMULO_VERSION
ARG ZOOKEEPER_VERSION

#ARG ACCUMULO_DOWNLOAD_URL="https://www.apache.org/dyn/closer.cgi?action=download&filename=accumulo/${ACCUMULO_VERSION}/accumulo-${ACCUMULO_VERSION}-bin.tar.gz"
ARG ACCUMULO_DOWNLOAD_URL="https://dlcdn.apache.org/accumulo/${ACCUMULO_VERSION}/accumulo-${ACCUMULO_VERSION}-bin.tar.gz"
ARG ACCUMULO_BACKUP_DOWNLOAD_URL="https://archive.apache.org/dist/accumulo/${ACCUMULO_VERSION}/accumulo-${ACCUMULO_VERSION}-bin.tar.gz"

ARG ZOOKEEPER_DOWNLOAD_URL="https://dlcdn.apache.org/zookeeper/zookeeper-${ZOOKEEPER_VERSION}/apache-zookeeper-${ZOOKEEPER_VERSION}-bin.tar.gz"
ARG ZOOKEEPER_BACKUP_DOWNLOAD_URL="https://archive.apache.org/dist/zookeeper/zookeeper-${ZOOKEEPER_VERSION}/apache-zookeeper-${ZOOKEEPER_VERSION}-bin.tar.gz"

USER root

RUN	yum -y update && \
	yum -y install \
		gcc-c++ \
		make \
		wget \
	&& yum clean all

ENV JAVA_HOME=/usr/lib/jvm/java
# Allow users to provide their own builds of Accumulo, ZooKeeper and Hadoop
COPY ./files/ .
# Otherwise, download official distributions
RUN cd / && \
    if [ ! -f "./accumulo-${ACCUMULO_VERSION}-bin.tar.gz" ]; then \
		  (wget -nv -O ./accumulo-${ACCUMULO_VERSION}-bin.tar.gz ${ACCUMULO_DOWNLOAD_URL} || wget -nv -O ./accumulo-${ACCUMULO_VERSION}-bin.tar.gz ${ACCUMULO_BACKUP_DOWNLOAD_URL}); \
		fi
RUN cd / && \
	if [ ! -f "./apache-zookeeper-${ZOOKEEPER_VERSION}-bin.tar.gz" ]; then \
		(wget -nv -O ./apache-zookeeper-${ZOOKEEPER_VERSION}-bin.tar.gz ${ZOOKEEPER_DOWNLOAD_URL} || wget -nv -O ./apache-zookeeper-${ZOOKEEPER_VERSION}-bin.tar.gz ${ZOOKEEPER_BACKUP_DOWNLOAD_URL}); \
	fi

# Extract required files
RUN cd / && \
    tar -xf ./accumulo-${ACCUMULO_VERSION}-bin.tar.gz accumulo-${ACCUMULO_VERSION}/bin/ accumulo-${ACCUMULO_VERSION}/lib/ && \
	rm -f ./accumulo-${ACCUMULO_VERSION}-bin.tar.gz && \
	accumulo-${ACCUMULO_VERSION}/bin/accumulo-util build-native

RUN \
	rm -rf ./hadoop-${HADOOP_VERSION}/share/hadoop/yarn && \
	tar -xf ./apache-zookeeper-${ZOOKEEPER_VERSION}-bin.tar.gz --wildcards "apache-zookeeper-${ZOOKEEPER_VERSION}-bin/lib/zookeeper*.jar" && \
	rm -f ./apache-zookeeper-${ZOOKEEPER_VERSION}-bin.tar.gz
	
RUN cd / && pwd && ls -al

FROM ${BASE_IMAGE_NAME}:${BASE_IMAGE_TAG}
ARG ACCUMULO_VERSION
ARG ZOOKEEPER_VERSION
ARG USER=accumulo
ARG GROUP=accumulo

USER root

RUN yum -y update && \
	yum -y install \
		wget \
	&& yum clean all
RUN wget -O /usr/bin/dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.2.5/dumb-init_1.2.5_x86_64
RUN chmod +x /usr/bin/dumb-init

RUN cd /
COPY --from=builder /accumulo-${ACCUMULO_VERSION} /opt/accumulo-${ACCUMULO_VERSION}/
COPY ./conf /opt/accumulo-${ACCUMULO_VERSION}/conf
COPY --from=builder /apache-zookeeper-${ZOOKEEPER_VERSION}-bin /opt/zookeeper-${ZOOKEEPER_VERSION}/

RUN groupadd ${GROUP} && useradd --gid ${GROUP} -G hadoop --no-create-home --shell /bin/bash ${USER}

RUN cd /opt \
	&& ln -s ./accumulo-${ACCUMULO_VERSION} ./accumulo \
	&& ln -s /usr/local/hadoop ./hadoop \
	&& ln -s ./zookeeper-${ZOOKEEPER_VERSION} ./zookeeper \
	&& mkdir -p -m 755 /var/log/accumulo \
	&& chown ${USER}:${GROUP} /var/log/accumulo \
	&& chown -LR ${USER}:${GROUP} ./accumulo \
	&& chown -LR ${USER}:${GROUP} ./zookeeper \
    && chown -h ${USER}:${GROUP} ./accumulo \
    && chown -h ${USER}:${GROUP} ./zookeeper \
	&& usermod -d /opt/accumulo ${USER}
	
COPY ./entrypoint.sh /
RUN chmod 777 /entrypoint.sh

USER ${USER}

ENV ACCUMULO_HOME=/opt/accumulo
ENV ACCUMULO_CONF_DIR=${ACCUMULO_HOME}/conf
ENV ACCUMULO_LOG_DIR=/var/log/accumulo
ENV ZOOKEEPER_HOME=/opt/zookeeper
ENV PATH=$ACCUMULO_HOME/bin:$PATH
ENV HADOOP_HOME=/usr/local/hadoop \
    HADOOP_COMMON_HOME=/usr/local/hadoop \
    HADOOP_HDFS_HOME=/usr/local/hadoop \
    HADOOP_MAPRED_HOME=/usr/local/hadoop \
    HADOOP_YARN_HOME=/usr/local/hadoop \
    HADOOP_CONF_DIR=/usr/local/hadoop/etc/hadoop \
    YARN_CONF_DIR=/usr/local/hadoop/etc/hadoop \
    JAVA_HOME=/usr/lib/jvm/java


ENTRYPOINT ["/entrypoint.sh", "accumulo"]
CMD ["help"]
