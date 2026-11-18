# Hadoop image

This image keeps the RPM layout used by the Hadoop and Accumulo Helm charts.
It retains HDFS, YARN, MapReduce, history server, router, proxy, JournalNode,
native shared and static libraries, headers, configuration, and daemon scripts.
The Java toolchain and other packages inherited from the base image are retained.

Native debug symbols are optional:

```bash
# Default: runtime packages, without hadoop-debuginfo.
docker build -t datawave-stack-hadoop:local datawave-hadoop/

# Include symbols when debugging native Hadoop code.
docker build --build-arg HADOOP_DEBUG_SYMBOLS=true \
  -t datawave-stack-hadoop:debug-local datawave-hadoop/
```

Use `datawave-hadoop/` as the build context. Its allowlist includes only the
Dockerfile and `bigtop.repo`. Credentials, private repository configuration,
logs, build outputs, and unrelated local files are excluded. Verify this with:

```bash
python3 scripts/check-hadoop-build-context.py
```

Private repository configuration is a BuildKit secret, mounted only while
installing packages:

```bash
docker build --secret id=artifactory_repo,src=/path/to/artifactory.repo \
  -t datawave-stack-hadoop:local datawave-hadoop/
```

The self-hosted workflow supplies the same secret. Public builds can omit it.

For a completely local parent image:

```bash
docker build -t local/datawave-stack-base:main datawave-base/
docker build --build-arg REGISTRY=local \
  -t datawave-stack-hadoop:rpm-pruned-local datawave-hadoop/
```

The repository configuration selects the RPM version; the existing
`HADOOP_VERSION` argument does not pin package resolution. At validation time,
the public Bigtop repository supplied Hadoop 3.3.5. Private repositories may
supply a different version.

Deploy and evaluate this image using the `hadoop` and `hadoop-config` charts in
`NationalSecurityAgency/datawave-helm-charts`. Deployment templates belong in
that repository. Its `tests/hadoop-image/` fixture exercises HDFS persistence,
distributed WordCount, and the ResourceManager/history endpoints before and
after an image upgrade.
