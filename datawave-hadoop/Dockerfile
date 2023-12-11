FROM ghcr.io/nationalsecurityagency/datawave-base-jdk-11:docker-images

# Add native libs
ARG HADOOP_VERSION=3.3.6
ADD bigtop.repo /etc/yum.repos.d/

RUN yum clean all && \
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
    hadoop-yarn hadoop-yarn-router hadoop-yarn-proxyserver hadoop-debuginfo \
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
    HADOOP_COMMON_HOME=/usr/local/hadoop \
    HADOOP_HDFS_HOME=/usr/local/hadoop-hdfs \
    HADOOP_MAPRED_HOME=/usr/local/hadoop-mapreduce \
    HADOOP_YARN_HOME=/usr/local/hadoop-yarn \
    HADOOP_CONF_DIR=/usr/local/hadoop/etc/hadoop \
    YARN_CONF_DIR=/usr/local/hadoop-yarn/etc/hadoop \
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
