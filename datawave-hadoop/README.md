# Hadoop image

This image preserves the RPM layout used by the Hadoop and Accumulo Helm charts,
including HDFS, YARN, MapReduce, history server, router, proxy, JournalNode,
native libraries, headers, configuration and daemon scripts. It inherits the
selected Java toolchain from the base target built in the same invocation.

Use the shared build command from the repository root:

```bash
# Build Java 11 and Java 17 base/Hadoop images from the private RPM repository.
python3 scripts/build-images.py --target hadoop \
  --repo-file datawave-hadoop/artifactory.repo

# Build from local Hadoop RPMs without Artifactory access.
python3 scripts/build-images.py --target hadoop --hadoop-source local \
  --rpm-dir /path/to/rpms

# Include native debug symbols under distinct -debug tags.
python3 scripts/build-images.py --target hadoop --java 17 --debug-symbols \
  --repo-file datawave-hadoop/artifactory.repo
```

Hadoop RPM versions are pinned by `build/versions.json` or `--hadoop-version`.
The public Bigtop repository supplies dependencies but excludes all Hadoop
packages. Runtime builds omit `hadoop-debuginfo`.

The Docker build context allows only `Dockerfile`, `install-hadoop.sh` and the
public `bigtop.repo`. Private repository configuration is a temporary BuildKit
secret. Selected local RPMs are provided through a separate named context.
Check Docker's actual context filtering with:

```bash
python3 scripts/check-hadoop-build-context.py
```

See the [root README](../README.md) for credentials, registry destinations,
image tags, cache refreshes and GitHub Actions setup. The build command always
builds its base target instead of pulling a pre-existing DataWave image.

Deploy and evaluate this image using the `hadoop` and `hadoop-config` charts in
`NationalSecurityAgency/datawave-helm-charts`. Its `tests/hadoop-image/` fixture
exercises HDFS persistence, distributed WordCount, and the ResourceManager and
history endpoints before and after an image upgrade. These deployment tests
complement the build command's runtime smoke tests.
