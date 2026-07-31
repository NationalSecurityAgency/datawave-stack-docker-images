# DataWave Stack Docker Images

This repository contains the Dockerfiles and GitHub Actions workflows used to build supporting container images for DataWave Helm Chart deployments. The images are published to GitHub Container Registry (GHCR) and are consumed by the DataWave Helm charts.

## Images

| Image | Build context | Purpose |
| --- | --- | --- |
| `datawave-stack-base` | `datawave-base/` | Provides the UBI 8 foundation, Java 11, and common system and build utilities used by the DataWave stack images. |
| `datawave-stack-hadoop` | `datawave-hadoop/` | Extends the base image with Hadoop, HDFS, MapReduce, and YARN packages and runtime configuration. |
| `datawave-stack-accumulo` | `datawave-accumulo/` | Extends the Hadoop image with Apache Accumulo, Apache ZooKeeper, native libraries, and the Accumulo runtime entrypoint. |
| `mysqlsh-no-root` | `mysqlsh-no-root/` | Adapts the MySQL Community Operator image so the MySQL Shell directory can be used without root-only permissions. |

The main DataWave image dependency chain is:

```text
datawave-stack-base -> datawave-stack-hadoop -> datawave-stack-accumulo
```

## Publishing

GitHub Actions builds and publishes the DataWave stack images to GHCR. Changes merged to `main` trigger the standard image build workflow, while the Accumulo workflow can build a selected Accumulo branch and publish a version-specific image tag. A separate self-hosted workflow publishes images to the configured private registry.

Before adding an image that uses a new GHCR package name, the package must be created by CI with package write permissions. See [Create New Container Packages](CREATE_NEW_PACKAGES.md) for the reason and instructions for running the package creation workflow.

## Testing Image Changes

Image changes are tested manually by building the affected image, assigning it a unique test tag, pushing it to GHCR, and configuring the DataWave Helm charts to pull that tag.

### Prerequisites

- Docker is installed and running.
- You have a GitHub personal access token with permission to write the target GHCR package.
- The GHCR package already exists. If it does not, follow [Create New Container Packages](CREATE_NEW_PACKAGES.md).
- You have access to a Kubernetes environment where the DataWave Helm charts can be deployed.

### Build and Push

Authenticate to GHCR. Store the token in `GHCR_TOKEN` and avoid placing it directly in shell history:

```bash
export GHCR_USER=<github-username>
export GHCR_TOKEN=<github-personal-access-token>
echo "$GHCR_TOKEN" | docker login ghcr.io --username "$GHCR_USER" --password-stdin
```

Choose a unique tag that identifies the change being tested:

```bash
export TEST_TAG=<github-username>-<change-description>
```

Build from the repository root and include the complete GHCR image name in the tag. For example, to test the Hadoop image:

```bash
docker build \
  --tag "ghcr.io/nationalsecurityagency/datawave-stack-hadoop:${TEST_TAG}" \
  ./datawave-hadoop

docker push "ghcr.io/nationalsecurityagency/datawave-stack-hadoop:${TEST_TAG}"
```

Use the same pattern for another image by changing both the package name and build context:

```bash
docker build --tag "ghcr.io/nationalsecurityagency/<package-name>:${TEST_TAG}" ./<build-context>
docker push "ghcr.io/nationalsecurityagency/<package-name>:${TEST_TAG}"
```

When a change affects multiple images in the dependency chain, build and push them in dependency order: base, Hadoop, then Accumulo. Ensure each dependent build references the intended parent image and tag.

### Test with Helm

1. Update the appropriate Helm image repository and tag values to reference the test image in `ghcr.io/nationalsecurityagency`.
2. Install or upgrade the Helm release in the test Kubernetes environment.
3. Confirm that Kubernetes successfully pulls the test tag from GHCR.
4. Verify that the affected pods start successfully and exercise the behavior changed by the image update.
5. Review pod events and container logs for image pull, startup, permission, or runtime errors.

Do not reuse a release tag for testing. A unique tag makes it clear which image is deployed and prevents a cached image from masking the latest build.
