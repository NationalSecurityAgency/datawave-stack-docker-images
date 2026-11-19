ARG REGISTRY="ghcr.io/nationalsecurityagency"
FROM ${REGISTRY}/datawave-stack-base:main

# Add native libs
ARG HADOOP_VERSION=3.4.1
# Native debugging is available when needed, without shipping symbols by default.
ARG HADOOP_DEBUG_SYMBOLS=false
COPY bigtop.repo /etc/yum.repos.d/

RUN --mount=type=secret,id=artifactory_repo,target=/etc/yum.repos.d/artifactory.repo \
    case "${HADOOP_DEBUG_SYMBOLS}" in \
        true) hadoop_debug_package=hadoop-debuginfo ;; \
        false) hadoop_debug_package="" ;; \
        *) echo "HADOOP_DEBUG_SYMBOLS must be true or false" >&2; exit 1 ;; \
    esac && \
    yum clean all && \
    rm -rf /var/cache/yum && \
    yum clean expire-cache && \
    yum makecache && \
    yum update -y && \
    yum install -y bigtop-utils \
    openssl \
    glibc \
    compat-openssl10 \
    lzo \
    protobuf-c \
    hadoop hadoop-hdfs hadoop-libhdfs hadoop-client \
    hadoop-yarn hadoop-yarn-router hadoop-yarn-proxyserver ${hadoop_debug_package} \
    hadoop-yarn-timelineserver hadoop-yarn-nodemanager hadoop-hdfs-journalnode \
    hadoop-mapreduce hadoop-mapreduce-historyserver && yum clean all && \
    rm -rf /var/cache/yum && \
    yum clean expire-cache && \
    usermod -u 1000 hdfs && \
    ln -fns /lib/hadoop /usr/local/hadoop && \
    ln -fns /lib/hadoop-hdfs /usr/local/hadoop-hdfs && \
    ln -fns /lib/hadoop-mapreduce /usr/local/hadoop-mapreduce && \
    ln -fns /lib/hadoop-yarn /usr/local/hadoop-yarn && \
    mkdir -p /usr/local/hadoop/logs && \
    mkdir -p /usr/local/hadoop-hdfs/logs && \
    mkdir -p /usr/local/hadoop-yarn/logs && \
    mkdir -p /var/lib/hadoop-yarn && \
    mkdir -p /var/log/hadoop-yarn && \
    mkdir -p /usr/local/hadoop/etc/hadoop && \
    mkdir -p /opt/hdfs/hadoop-yarn/cache/hadoop/nm-local-dir && \
    mkdir -p /usr/local/hadoop/hdfs && \
    mkdir -p /usr/lib/hadoop/data && \
    chown hdfs:hdfs -R /usr/local/hadoop/* && \
    chown hdfs:hdfs -R /lib/hadoop/* && \
    chown hdfs:hdfs -R /lib/hadoop-hdfs/* && \
    chown hdfs:hdfs -R /lib/hadoop-yarn/* && \
    chown hdfs:hdfs -R /lib/hadoop-mapreduce/* && \
    chown hdfs:hdfs -R /var/lib/hadoop* && \
    chown hdfs:hdfs -R /var/log/hadoop* && \
    chmod 777 -R /etc/hadoop/ && \
    chmod 777 -R /opt/hdfs/hadoop-yarn && \
    rm -Rf /usr/lib/hadoop/tools

USER hadoop

ENV HADOOP_HOME=/usr/local/hadoop \
    PATH=${PATH}:/usr/local/hadoop/bin:/usr/local/hadoop-hdfs/bin

# Hdfs ports
EXPOSE 50010 50020 50070 50075 50090 8020 9000
# Mapred ports
EXPOSE 19888
#Yarn ports
EXPOSE 8030 8031 8032 8033 8040 8042 8088
#Other ports
EXPOSE 49707 2122

USER hdfs
