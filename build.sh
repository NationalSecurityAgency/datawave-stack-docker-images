#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_usage() {
cat <<EOF
Usage: build <IMAGES...> [OPTIONS]

Description:
Builds the datawave-stack images locally in a pre-defined order.

Images:
  base        Builds the datawave-base image
  hadoop      Builds the datawave-hadoop image
  accumulo    Builds the datawave-accumulo image
  all         Builds the base, hadoop, and accumulo images

Options:
  -h, --help  Display usage
EOF
}

invalid_args() {
  echo -e "Invalid arguments: $1\n"
  print_usage 1>&2
  exit 1
}

set_build_order() {
  local -n input_ref=$1
  local -n output_ref=$2

  local build_order=("base" "hadoop" "accumulo")

  if [[ "${input_ref[0]}" == "all" ]]; then
    output_ref+=("${build_order[@]}")
    return 0
  fi

  local -A count_map
  for item in "${input_ref[@]}"; do
    (( count_map["$item"]++ ))
  done

  for item in "${build_order[@]}"; do
    if [[ ${count_map[$item]:-0} -gt 0 ]]; then
      output_ref+=("$item")
    fi
  done
}

build_base() {
  build_image "datawave-base" "ghcr.io/nationalsecurityagency/datawave-stack-base:main"
}

build_hadoop() {
  build_image "datawave-hadoop" "ghcr.io/nationalsecurityagency/datawave/datawave-stack-hadoop:main"
}

build_accumulo() {
  build_image "datawave-accumulo" "ghcr.io/nationalsecurityagency/datawave-stack-accumulo:4.0.0-SNAPSHOT"
}

build_image() {
  docker build "${SCRIPT_DIR}/$1" --tag "$2"
}

main() {
  if [[ -z $1 ]]; then
    invalid_args "No images specified"
  fi

  # Parse the arguments.
  local all_flag=false
  local images=()
  for arg in "${@}"; do
    case "$arg" in
      # If all is specified, we want this to be the only element in the images array.
      all)
        all_flag='true'
        images=("all")
        ;;
      # Include the image 'base'.
      base)
        if [[ $all_flag != 'true' ]]; then
          images+=("base")
        fi
        ;;
      # Include the image 'hadoop'.
      hadoop)
        if [[ $all_flag != 'true' ]]; then
          images+=("hadoop")
        fi
        ;;
      # Include the image 'accumulo'
      accumulo)
        if [[ $all_flag != 'true' ]]; then
          images+=("accumulo")
        fi
        ;;
      -h | --help)
        print_usage
        exit 0
        ;;
      *)
        invalid_args "'$arg' is an invalid argument"
        ;;
    esac
  done

  # Establish the correct order to build the images.
  local images_to_build=()
  set_build_order images images_to_build

  # Build each image.
  for image in "${images_to_build[@]}"; do
    "build_${image}"
  done
}

main "$@"
