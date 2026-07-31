# Create New Container Packages

Use the **Create packages** GitHub Actions workflow to create new container package names in the `nationalsecurityagency` organization before a collaborator can push to them manually.

## Why This Workflow Is Needed

GitHub does not allow a user to directly create a new container package in this organization when that package does not already exist. The package must first be created by a CI job with permission to write packages.

The workflow uses the repository's `GITHUB_TOKEN` with `packages: write` permission to build and push an initial image to GitHub Container Registry (GHCR). That first push creates the package under the organization. Afterward, the package can be configured in GitHub and used by the normal build and publishing workflows.

## Run the Workflow

1. Open this repository on GitHub.
2. Select the **Actions** tab.
3. Select **Create packages** from the workflow list.
4. Select **Run workflow**.
5. Choose the branch whose name should be used as the initial image tag.
6. In **Comma separated list of package names to create**, enter one or more package names.
7. Select **Run workflow** and wait for every matrix job to complete successfully.

Enter only package names, without the registry, organization, or image tag. Separate multiple names with commas and do not add spaces.

For example:

```text
datawave/datawave-stack-hadoop,datawave/datawave-stack-mysql
```

If the workflow is run from the `main` branch, this example pushes:

```text
ghcr.io/nationalsecurityagency/datawave/datawave-stack-hadoop:main
ghcr.io/nationalsecurityagency/datawave/datawave-stack-mysql:main
```

## What the Workflow Does

For each package name, the workflow:

1. Checks out the repository.
2. Authenticates to `ghcr.io` using the workflow's `GITHUB_TOKEN`.
3. Builds the `datawave-base` image as an initial placeholder image.
4. Pushes that image to `ghcr.io/nationalsecurityagency/<package-name>:<branch-name>`.

The placeholder image exists to create the package entry. The package's normal image workflow can replace it with the intended image and tags later.

## After the Workflow Completes

1. Open the organization package page and confirm that each package exists.
2. Configure the package visibility, access, and repository linkage as required.
3. Run or update the normal image workflow that publishes the intended image to the new package.

If a package is not created, open the failed workflow run and check that the package name contains no spaces and that the job retained `packages: write` permission.
