# syntax=docker/dockerfile:1
ARG BASE_IMAGE=stack-base
FROM ${BASE_IMAGE}

ARG HADOOP_VERSION=3.4.3
ARG HADOOP_SOURCE=repo
ARG HADOOP_DEBUG_SYMBOLS=false

COPY install-hadoop.sh /usr/local/bin/install-hadoop
COPY bigtop.repo /etc/yum.repos.d/bigtop.repo
# local-rpms is a named context, empty unless local RPMs are supplied.
# Repository configuration, caches and logs exist only for this instruction.
RUN --mount=type=secret,id=artifactory_repo,target=/etc/yum.repos.d/artifactory.repo \
    --mount=type=bind,from=local-rpms,source=.,target=/mnt/rpms \
    --mount=type=tmpfs,target=/var/log \
    --mount=type=tmpfs,target=/var/cache/dnf \
    --mount=type=tmpfs,target=/var/cache/yum \
    --mount=type=tmpfs,target=/var/lib/dnf \
    bash /usr/local/bin/install-hadoop "${HADOOP_SOURCE}" "${HADOOP_VERSION}" "${HADOOP_DEBUG_SYMBOLS}"

RUN test ! -e /etc/yum.repos.d/artifactory.repo && \
    usermod -u 1000 hdfs && \
    ln -fns /lib/hadoop /usr/local/hadoop && \
    ln -fns /lib/hadoop-hdfs /usr/local/hadoop-hdfs && \
    ln -fns /lib/hadoop-mapreduce /usr/local/hadoop-mapreduce && \
    ln -fns /lib/hadoop-yarn /usr/local/hadoop-yarn && \
    mkdir -p /usr/local/hadoop/logs /usr/local/hadoop-hdfs/logs /usr/local/hadoop-yarn/logs \
        /var/lib/hadoop-yarn /var/log/hadoop-yarn /usr/local/hadoop/etc/hadoop \
        /opt/hdfs/hadoop-yarn/cache/hadoop/nm-local-dir /usr/local/hadoop/hdfs /usr/lib/hadoop/data && \
    chown -R hdfs:hdfs /usr/lib/hadoop* /var/lib/hadoop* /var/log/hadoop* && \
    chmod -R 777 /etc/hadoop /opt/hdfs/hadoop-yarn && \
    rm -rf /usr/lib/hadoop/tools && \
    rpm -qa | sort > /rpm-manifest.txt

ENV HADOOP_HOME=/usr/local/hadoop \
    PATH=${PATH}:/usr/local/hadoop/bin:/usr/local/hadoop-hdfs/bin

EXPOSE 50010 50020 50070 50075 50090 8020 9000 19888
EXPOSE 8030 8031 8032 8033 8040 8042 8088 49707 2122
USER hdfs
