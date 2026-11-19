#!/usr/bin/env python3
"""Exercise Docker's actual context filtering, without network or private data."""

import shutil
import subprocess
import tempfile
from pathlib import Path


root = Path(__file__).resolve().parent.parent
allowed = {"Dockerfile", "install-hadoop.sh", "bigtop.repo"}
unwanted = [
    "artifactory.repo", ".env", ".git/config", ".kube/config",
    "credentials.pem", "build.log", "target/application.jar",
    "local-rpms/hadoop-3.4.3.rpm", "files/agent.jar", "bigtop.repo.bak",
]
with tempfile.TemporaryDirectory(prefix="hadoop-context-check-") as temporary:
    directory = Path(temporary)
    context = directory / "context"
    context.mkdir()
    for name in sorted(allowed) + unwanted:
        path = context / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic build-context input\n")
    dockerfile = directory / "check.Dockerfile"
    dockerfile.write_text("FROM scratch\nCOPY . /inputs/\n")
    shutil.copyfile(root / "datawave-hadoop/.dockerignore", str(dockerfile) + ".dockerignore")
    output = directory / "output"
    subprocess.run(
        ["docker", "buildx", "build", "--progress=plain", "-f", str(dockerfile),
         "--output", "type=local,dest=" + str(output), str(context)], check=True)
    actual = {
        str(path.relative_to(output / "inputs"))
        for path in (output / "inputs").rglob("*") if path.is_file()
    }
    if actual != allowed:
        raise SystemExit("Unexpected context: {}".format(sorted(actual)))
    print("Hadoop context: Dockerfile, install-hadoop.sh and public bigtop.repo only.")
