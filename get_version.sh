#!/bin/bash

set -eu

# This script generate version from git tags (only from annotated tags)
# Example of the output of the script:
#
#   $ git tag -a 0.1.0 -m "0.1.0"
#
#   $ bash get_version.sh
#   0.1.0
#
#   $ echo "Lorem ipsum" > example_file
#   $ git add example_file
#   $ git commit -m "Add file"
#   [ng de9d514] feature commit
#    1 file changed, 1 insertion(+), 1 deletion(-)
#
#   $ bash get_version.sh
#   0.1.1-SNAPSHOT
#
#   $ git checkout -b feature/APPCONSOLE-123
#   Switched to a new branch 'feature/APPCONSOLE-123'
#
#   $ bash get_version.sh
#   0.1.1-feature-APPCONSOLE-123-SNAPSHOT
#
#   $ git checkout ng
#   Switched to branch 'ng'
#
#   $ git tag -a 0.1.1 -m "0.1.1"
#   $ bash ~/workspace/version-bash/get_version.sh
#   0.1.1

if [[ "$OSTYPE" == "darwin"* ]]; then
    sed_command="gsed"
else
    sed_command="sed"
fi

current_branch=$(git rev-parse --abbrev-ref HEAD)

die(){
    echo "$1"
    exit 2
}

show_version(){
    echo "$1"
    exit 0
}

# bump PATH number of version complies with semantic versioning
# version format MAJOR.MINOR.PATCH - http://semver.org/
generate_next_version(){
    current_dateversion=$(echo "$1" | cut -d '.' -f1)
    current_path_number=$(echo "$1" | cut -d '.' -f2)
    new_dateversion=$(date +"%Y%m%d")

    if [[ $current_dateversion ==  $new_dateversion ]]; then
        incremented_patch=$((current_path_number+1))
    else
        incremented_patch="1"
    fi

    next_version="${new_dateversion}.${incremented_patch}"
}


if [ -z "$current_branch" ]; then
    die "Empty commits list on this branch or you didn't commit anything"
fi

current_tag=$(git describe)

if [ -z "$current_tag" ]; then
    die "you don't have any tag on branch : ${current_branch}"
fi

# check if any of commit has been added after last tag
changes_above_tag=$(echo $current_tag | $sed_command -r '/^.*-[0-9]+-[a-z0-9].*/p' | wc -l | xargs)

clean_tag=$(git describe --abbrev=0)


if [[ "$current_branch" == "ng" ]]; then
    if [ "$changes_above_tag" == 1 ]; then
        version="${clean_tag}"
    else
        generate_next_version "$clean_tag"
        bumped_clean_tag="$next_version"
        version="${bumped_clean_tag}-SNAPSHOT"
    fi
else
    generate_next_version "$clean_tag"
    bumped_clean_tag="$next_version"
    # Sanitize version - all characters that do not match [A-Za-z0-9._-]
    # group are replaced with `-`
    sanitized_branch_name=$(echo $current_branch | $sed_command 's/[^a-zA-Z0-9]/-/g')
    version="${bumped_clean_tag}-${sanitized_branch_name}-SNAPSHOT"
fi
show_version "$version"
