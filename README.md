# DataWave stack images

Build Java 11 and Java 17 variants of the complete chain:

```text
UBI 8 + Corretto JDK -> Hadoop RPMs -> Accumulo + ZooKeeper
```

Every build constructs its own base and Hadoop images. Docker Buildx Bake
connects the build targets directly; it does not pull an existing DataWave
Hadoop image. Docker's local build cache can still reuse unchanged layers.

The same command runs on developer machines and self-hosted GitHub runners.
RPM source and publish destination are independent. An Artifactory build can
publish to GHCR, a private registry, or both.

## Build locally

Requirements: Python 3.9+, Docker with Buildx/Bake and BuildKit support for named
contexts, and a Linux amd64 builder. The existing native packages and dumb-init
binary target amd64. Public access to UBI, Corretto, EPEL and Apache downloads is
also needed; local RPM mode is not a fully offline build.

With Artifactory access, copy
[`artifactory.repo.example`](datawave-hadoop/artifactory.repo.example) to
`datawave-hadoop/artifactory.repo`, configure the repository, signing key and
credentials, then run:

```bash
python3 scripts/build-images.py --repo-file datawave-hadoop/artifactory.repo
```

This builds both Java runtimes and loads the images into Docker. Nothing is
pushed unless `--push` is given. Select one runtime with `--java 11` or
`--java 17`. Use `--target hadoop` to stop after base and Hadoop.

Without Artifactory access, obtain the Hadoop RPM bundle from a teammate or an
accessible artifact store, then use:

```bash
python3 scripts/build-images.py --hadoop-source local --rpm-dir /path/to/rpms
```

Only the selected runtime packages are staged in a temporary named context.
Missing packages and duplicate versions fail before building. The required
Hadoop package names are listed in `HADOOP_PACKAGES` in
[`scripts/build-images.py`](scripts/build-images.py). Supply the version in
`build/versions.json` or override it with `--hadoop-version`. The RPMs must use
the Bigtop layout for EL8. The public Bigtop repository supplies dependencies
(such as utilities, jsvc, Groovy and ZooKeeper) and excludes all `hadoop*`
packages; it cannot supply a different Hadoop version. You may also
include a `bigtop-utils` RPM in the local bundle. Extra dependency repositories can be supplied using
`--repo-file` in local mode too.

The old `datawave-hadoop/build-local.sh RPM_DIR IMAGE_TAG` command delegates to
this build and preserves its optional local tag. `JAVA_VERSION` defaults to 11.

## Publish

Log in to each destination using `docker login HOST`, then repeat `--registry`
for each destination namespace:

```bash
python3 scripts/build-images.py \
  --repo-file datawave-hadoop/artifactory.repo \
  --registry ghcr.io/nationalsecurityagency \
  --registry registry.example.com/datawave \
  --push
```

The registry argument includes the namespace, but no scheme or trailing slash.
Login uses only the host. Images are built once, loaded, smoke tested, then the
same images are pushed to all requested destinations. A failed build or smoke
test prevents every push for that invocation. A registry outage during
publication can still leave a partially published set; rerun after resolving it.

## Versions and tags

[`build/versions.json`](build/versions.json) is the default version configuration
for automation. Override with `--hadoop-version`, `--accumulo-version` or
`--zookeeper-version`. Hadoop packages are pinned to that version and checked
after installation; a different RPM version cannot silently receive the tag.

For the defaults, each destination receives:

| Image | Tags (Java 11 example) |
| --- | --- |
| `datawave-stack-base` | `java11`, `11` |
| `datawave-stack-hadoop` | `3.4.3-java11` |
| `datawave-stack-accumulo` | `2.1.6-java11`, `2.1.6-hadoop3.4.3-zk3.8.8-java11` |

Java 17 gets separate `java17` tags. There is no ambiguous `main` or `latest`
alias; update chart image tags explicitly. Tags can be refreshed by rebuilds;
pin image digests in deployments that require immutable artifacts.

`--tag my-test` replaces the Accumulo tag prefix, producing
`my-test-java11` and a tag with the Hadoop/ZooKeeper versions. It leaves parent
image tags versioned. Use a separate destination namespace for isolated tests.
`--debug-symbols` includes `hadoop-debuginfo` and appends `-debug` to Hadoop
and Accumulo tags. Runtime builds omit it.

To package your own Accumulo binary distribution, place
`accumulo-VERSION-bin.tar.gz` in `datawave-accumulo/files/` and pass
`--accumulo-version VERSION --tag VERSION-dwv-COMMIT`. The same directory accepts
`apache-zookeeper-VERSION-bin.tar.gz`. Otherwise Apache binaries are downloaded.
For source changes, choose a tag distinct from a released build.

Use `--print` to inspect the generated Bake plan without building and
`--no-cache` to refresh cached package installs. BuildKit secrets do not
invalidate caches when their contents change; use `--no-cache` after changing
repository contents or configuration if the versions stay the same.

## GitHub Actions setup

All image jobs use self-hosted Linux x64 runners with Docker, network access to
Artifactory and the destinations, and Maven for source builds. Java compiler
setup is handled by the workflow. Configure these repository settings:

| Setting | Type | Purpose |
| --- | --- | --- |
| `HADOOP_REPO_CONFIG` | Secret | Complete yum repo file, including credentials and any required dependency repositories |
| `SELF_HOSTED_REGISTRY_ROOT` | Variable | Private registry host, e.g. `registry.example.com` |
| `SELF_HOSTED_REGISTRY` | Variable | Private namespace, e.g. `registry.example.com/datawave` |
| `CY_ROBOT_ACCOUNT_USER` | Secret | Private registry username |
| `CY_ROBOT_ACCOUNT_SECRET` | Secret | Private registry password/token |
| `IMAGE_RUNNER_LABELS` | Optional variable | JSON label array; defaults to `["self-hosted","linux","x64"]` |

The old `ARTIFACTORY_TOKEN` alone is replaced by `HADOOP_REPO_CONFIG`, so the
repository URL and credentials no longer need to be hard-coded in public YAML.
For example, an authorized maintainer can configure it from a local file:

```bash
gh secret set HADOOP_REPO_CONFIG < datawave-hadoop/artifactory.repo
```

- **Build release images** runs on relevant changes to `main`, weekly, or
  manually. Manual runs select Java and GHCR/private/both destinations.
- **Build Accumulo from source** runs nightly against `apache/accumulo:2.1` or
  manually against a repository/ref. It builds the distribution with the
  selected compiler JDK, then builds the full image chain. Source image tags
  contain the Maven version, Accumulo commit and runtime Java version. Select
  only compatible runtimes for branches that require a newer Java baseline.
- Automatic runs publish to both destinations when `SELF_HOSTED_REGISTRY` is
  configured, otherwise GHCR. Private-only builds are available manually.
- **Validate build automation** runs on GitHub-hosted runners for pull requests
  and `main`. PR jobs do not receive private build secrets or use self-hosted
  runners.

GHCR login uses `GITHUB_TOKEN` with `packages: write`; new packages are created
by the first real image push. Organization policy and existing package access
must allow the workflow to publish. Set the GHCR packages' visibility to public
after initial creation if needed, and link existing packages to this repository.

## Repository configuration and validation

Private repo files are excluded from the build context and mounted as BuildKit
secrets only during RPM installation. Yum/dnf logs, cache and history use
temporary mounts, so credentials and repository configuration are not copied
into a layer and later deleted. RPM install output is suppressed when private
repository configuration is present because failed downloads may include
authenticated URLs. On failure, check repository access,
package availability and dependencies outside the public CI log.

Every image contains `/rpm-manifest.txt`. The build command checks Java runtime,
Hadoop RPM version, Accumulo startup/version and native library presence,
ZooKeeper libraries/scripts, and absence of private repo files before publishing.
Accumulo's classpath supports the Hadoop RPM client directory and excludes
competing logging providers and the Hadoop bundle's ZooKeeper jars.
These are build smoke tests; they do not replace the HDFS/YARN/Accumulo deployment
tests in the Helm repository.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check-hadoop-build-context.py
```

The other image directories, such as `mysqlsh-no-root`, retain their independent
Dockerfiles and are outside the stack build command.
