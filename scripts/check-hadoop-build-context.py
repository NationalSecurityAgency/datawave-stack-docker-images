#!/usr/bin/env python3
"""Check Docker's actual context filtering with synthetic local files."""

import shutil
import subprocess
import tempfile
from pathlib import Path


root = Path(__file__).resolve().parent.parent
allowed = {"Dockerfile", "bigtop.repo"}
unwanted = [
    "artifactory.repo", ".env", ".git/config", ".kube/config",
    "credentials.pem", "build.log", "target/application.jar",
    "conf/local.xml", "bigtop.repo.bak",
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
    shutil.copyfile(
        str(root / "datawave-hadoop/.dockerignore"),
        str(dockerfile) + ".dockerignore",
    )
    output = directory / "output"
    result = subprocess.run(
        ["docker", "build", "--progress=plain", "-f", str(dockerfile),
         "--output", "type=local,dest=" + str(output), str(context)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    if result.returncode:
        raise SystemExit(result.stdout.decode(errors="replace"))
    actual = {
        str(path.relative_to(output / "inputs"))
        for path in (output / "inputs").rglob("*") if path.is_file()
    }
    if actual != allowed:
        raise SystemExit("Unexpected context: {}".format(sorted(actual)))
    print("Hadoop context: Dockerfile and bigtop.repo only; local files excluded.")
