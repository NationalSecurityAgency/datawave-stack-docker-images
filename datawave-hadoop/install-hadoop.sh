#!/usr/bin/env bash
set -euo pipefail

source_mode=$1
version=$2
debug_symbols=$3
packages=(hadoop hadoop-hdfs hadoop-libhdfs hadoop-client
  hadoop-yarn hadoop-yarn-router hadoop-yarn-proxyserver
  hadoop-yarn-timelineserver hadoop-yarn-nodemanager hadoop-hdfs-journalnode
  hadoop-mapreduce hadoop-mapreduce-historyserver)
case "$debug_symbols" in
  true) packages+=(hadoop-debuginfo) ;;
  false) ;;
  *) echo 'HADOOP_DEBUG_SYMBOLS must be true or false' >&2; exit 1 ;;
esac

install_inputs=()
case "$source_mode" in
  repo)
    test -s /etc/yum.repos.d/artifactory.repo || {
      echo 'Repository builds require the artifactory_repo BuildKit secret.' >&2
      exit 1
    }
    for package in "${packages[@]}"; do install_inputs+=("${package}-${version}"); done
    ;;
  local)
    shopt -s nullglob
    for package in "${packages[@]}"; do
      matches=(/mnt/rpms/"${package}-${version}-"*.rpm)
      if (( ${#matches[@]} != 1 )); then
        echo "Expected exactly one ${package}-${version} RPM; found ${#matches[@]}." >&2
        exit 1
      fi
      install_inputs+=("${matches[0]}")
    done
    utils=(/mnt/rpms/bigtop-utils-*.rpm)
    install_inputs+=("${utils[@]}")
    ;;
  *) echo 'HADOOP_SOURCE must be repo or local' >&2; exit 1 ;;
esac

# Repository URLs can appear in yum output. Logs, cache and history are tmpfs.
if ! yum -y --setopt=install_weak_deps=False install \
    bigtop-utils openssl glibc compat-openssl10 lzo protobuf-c \
    "${install_inputs[@]}" > /var/log/hadoop-install.log 2>&1; then
  echo 'Hadoop RPM installation failed. Check repository access, dependencies and the requested version.' >&2
  if [[ ! -s /etc/yum.repos.d/artifactory.repo ]]; then
    cat /var/log/hadoop-install.log >&2
  fi
  exit 1
fi
for package in "${packages[@]}"; do
  installed=$(rpm -q --qf '%{VERSION}' "$package")
  test "$installed" = "$version" || {
    echo "$package version mismatch: expected $version, installed $installed" >&2
    exit 1
  }
done
if [[ "$debug_symbols" == false ]] && rpm -q hadoop-debuginfo >/dev/null 2>&1; then
  echo 'Unexpected Hadoop debug symbols in runtime image.' >&2
  exit 1
fi
