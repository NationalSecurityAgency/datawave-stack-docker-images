#!/usr/bin/env python3
"""Build, verify, then optionally publish the same images locally and in CI."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
VERSIONS = json.loads((ROOT / "build/versions.json").read_text())
HADOOP_PACKAGES = (
    "hadoop", "hadoop-hdfs", "hadoop-libhdfs", "hadoop-client",
    "hadoop-yarn", "hadoop-yarn-router", "hadoop-yarn-proxyserver",
    "hadoop-yarn-timelineserver", "hadoop-yarn-nodemanager",
    "hadoop-hdfs-journalnode", "hadoop-mapreduce", "hadoop-mapreduce-historyserver",
)


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java", choices=("11", "17", "both"), default="both")
    parser.add_argument("--hadoop-source", choices=("repo", "local"), default="repo")
    parser.add_argument("--target", choices=("accumulo", "hadoop"), default="accumulo")
    parser.add_argument("--registry", action="append",
                        help="Destination namespace, repeat for multiple registries (default: local)")
    parser.add_argument("--repo-file", type=Path,
                        help="Yum repo file passed as a BuildKit secret; alternatively set HADOOP_REPO_CONFIG")
    parser.add_argument("--rpm-dir", type=Path, help="Local Hadoop RPM directory")
    parser.add_argument("--debug-symbols", action="store_true")
    for name, version in VERSIONS.items():
        parser.add_argument("--" + name + "-version", default=version)
    parser.add_argument("--tag", help="Override Accumulo tag prefix, e.g. my-test or 2.1.6-dwv-abcdef")
    parser.add_argument("--revision", default="", help="Image recipe commit for the OCI revision label")
    parser.add_argument("--source-url", default="https://github.com/NationalSecurityAgency/datawave-stack-docker-images")
    parser.add_argument("--push", action="store_true", help="Publish only after smoke tests pass")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--print", action="store_true", dest="print_plan", help="Print the Bake plan without building")
    args = parser.parse_args(argv)
    args.registry = args.registry or ["local"]
    for registry in args.registry:
        if not re.fullmatch(r"[a-z0-9][a-z0-9.:-]*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*", registry):
            parser.error("Registry must be a lowercase host/namespace without a scheme or trailing slash")
    for value in (args.hadoop_version, args.accumulo_version, args.zookeeper_version, args.tag):
        if value is not None and not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,79}", value):
            parser.error("Versions and tags must be Docker tag components of at most 80 characters")
    if args.hadoop_source != "local" and args.rpm_dir:
        parser.error("--rpm-dir requires --hadoop-source local")
    if args.repo_file and not args.repo_file.is_file():
        parser.error("--repo-file must name an existing file")
    if args.hadoop_source == "repo" and not (args.repo_file or os.environ.get("HADOOP_REPO_CONFIG")):
        parser.error("Repository builds require --repo-file or HADOOP_REPO_CONFIG")
    if args.hadoop_source == "local" and not (args.rpm_dir and args.rpm_dir.is_dir()):
        parser.error("Local builds require --rpm-dir")
    return args


def selected_rpms(args):
    """Allow only the exact requested runtime packages into the named context."""
    packages = list(HADOOP_PACKAGES)
    if args.debug_symbols:
        packages.append("hadoop-debuginfo")
    selected = []
    for package in packages:
        matches = sorted(args.rpm_dir.glob(f"{package}-{args.hadoop_version}-*.rpm"))
        if len(matches) != 1 or not matches[0].is_file():
            raise ValueError(f"Expected exactly one {package}-{args.hadoop_version} RPM; found {len(matches)}")
        selected.extend(matches)
    # bigtop-utils may be supplied alongside local Hadoop builds.
    utils = sorted(args.rpm_dir.glob("bigtop-utils-*.rpm"))
    if len(utils) > 1:
        raise ValueError("Expected at most one bigtop-utils RPM")
    return selected + utils


def plan(args, rpm_context=None):
    targets = {}
    java_versions = ("11", "17") if args.java == "both" else (args.java,)
    for java in java_versions:
        suffix = f"java{java}" + ("-debug" if args.debug_symbols else "")

        def target(component, versions):
            tags = list(dict.fromkeys(
                f"{registry}/datawave-stack-{component}:{version}"
                for registry in args.registry for version in versions
            ))
            if any(len(tag.rsplit(":", 1)[1]) > 128 for tag in tags):
                raise ValueError("Generated image tag exceeds Docker's 128 character limit")
            labels = {"org.opencontainers.image.source": args.source_url}
            if args.revision:
                labels["org.opencontainers.image.revision"] = args.revision
            return {
                "context": str(ROOT / f"datawave-{component}"),
                "dockerfile": "Dockerfile",
                "platforms": ["linux/amd64"],
                "tags": tags,
                "labels": labels,
                "args": {"JAVA_VERSION": java},
            }

        base_name, hadoop_name = f"base-{java}", f"hadoop-{java}"
        targets[base_name] = target("base", [f"java{java}", java])
        hadoop = target("hadoop", [f"{args.hadoop_version}-{suffix}"])
        hadoop["args"].update(BASE_IMAGE="stack-base", HADOOP_VERSION=args.hadoop_version,
                              HADOOP_SOURCE=args.hadoop_source,
                              HADOOP_DEBUG_SYMBOLS=str(args.debug_symbols).lower())
        hadoop["contexts"] = {
            "stack-base": f"target:{base_name}",
            "local-rpms": str(rpm_context or ROOT / "build/empty"),
        }
        if args.repo_file:
            hadoop["secret"] = [f"id=artifactory_repo,src={args.repo_file.resolve()}"]
        elif os.environ.get("HADOOP_REPO_CONFIG"):
            hadoop["secret"] = ["id=artifactory_repo,env=HADOOP_REPO_CONFIG"]
        targets[hadoop_name] = hadoop

        if args.target == "accumulo":
            # Custom/source builds must not overwrite the released version tags.
            prefix = args.tag or args.accumulo_version
            versions = [f"{prefix}-{suffix}",
                        f"{prefix}-hadoop{args.hadoop_version}-zk{args.zookeeper_version}-{suffix}"]
            accumulo = target("accumulo", versions)
            accumulo["args"].update(HADOOP_IMAGE="stack-hadoop", ACCUMULO_VERSION=args.accumulo_version,
                                    ZOOKEEPER_VERSION=args.zookeeper_version)
            accumulo["contexts"] = {"stack-hadoop": f"target:hadoop-{java}"}
            targets[f"accumulo-{java}"] = accumulo
    return {"group": {"default": {"targets": list(targets)}}, "target": targets}


def run(command, **kwargs):
    subprocess.run(command, check=True, **kwargs)


def smoke_tests(build_plan, args):
    for name, target in build_plan["target"].items():
        component, java = name.split("-")
        image = target["tags"][0]
        script = r"""
set -euo pipefail
actual=$(java -XshowSettings:properties -version 2>&1 | sed -n 's/^[[:space:]]*java.specification.version = //p')
test "$actual" = "$1"
test -s /rpm-manifest.txt
test ! -e /etc/yum.repos.d/artifactory.repo
test ! -e /var/log/hadoop-install.log
"""
        if component != "base":
            script += r"""
test "$(rpm -q --qf '%{VERSION}' hadoop)" = "$2"
hadoop version
if [ "$4" = false ]; then ! rpm -q hadoop-debuginfo >/dev/null 2>&1; fi
"""
        if component == "accumulo":
            script += r"""
test -f "/opt/accumulo/lib/accumulo-core-$3.jar"
test -s /opt/accumulo/lib/native/libaccumulo.so
test -f "/opt/zookeeper/lib/zookeeper-$5.jar"
test -x /opt/zookeeper/bin/zkServer.sh
accumulo version
"""
        run(["docker", "run", "--rm", "--network", "none", "--entrypoint", "bash", image,
             "-c", script, "smoke", java, args.hadoop_version, args.accumulo_version,
             str(args.debug_symbols).lower(), args.zookeeper_version])


def main(argv=None):
    args = arguments(argv)
    with tempfile.TemporaryDirectory(prefix="datawave-build-") as temporary:
        directory = Path(temporary)
        rpm_context = None
        if args.hadoop_source == "local":
            rpm_context = directory / "rpms"
            rpm_context.mkdir()
            for rpm in selected_rpms(args):
                shutil.copyfile(rpm, rpm_context / rpm.name)
        build_plan = plan(args, rpm_context)
        if args.print_plan:
            print(json.dumps(build_plan, indent=2))
            return
        bake_file = directory / "bake.json"
        bake_file.write_text(json.dumps(build_plan))
        command = ["docker", "buildx", "bake", "--file", str(bake_file), "--load"]
        if rpm_context:
            command.append(f"--allow=fs.read={rpm_context}")
        if args.no_cache:
            command.append("--no-cache")
        run(command, cwd=ROOT)
        smoke_tests(build_plan, args)
        if args.push:
            for target in build_plan["target"].values():
                for tag in target["tags"]:
                    run(["docker", "push", tag])
        print("Built and verified:" + (" (published)" if args.push else " (local only)"))
        for target in build_plan["target"].values():
            for tag in target["tags"]:
                print("  " + tag)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
