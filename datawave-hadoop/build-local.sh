#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
rpm_dir=${1:-"${script_dir}/../../dwp-rpm-builds/hadoop/build_output_rocky8/RPMS/x86_64"}
image_tag=${2:-datawave-stack-hadoop:local}
java_version=${JAVA_VERSION:-11}
hadoop_version=${HADOOP_VERSION:-$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["hadoop"])' "${script_dir}/../build/versions.json")}

python3 "${script_dir}/../scripts/build-images.py" \
  --java "${java_version}" --target hadoop --hadoop-source local \
  --rpm-dir "${rpm_dir}" --hadoop-version "${hadoop_version}"
docker tag "local/datawave-stack-hadoop:${hadoop_version}-java${java_version}" "${image_tag}"
