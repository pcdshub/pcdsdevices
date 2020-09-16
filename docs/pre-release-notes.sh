#!/bin/bash

ISSUE=$1
DESCRIPTION=$2

if [[ -z "$ISSUE" || -z "$DESCRIPTION" ]]; then
    echo "Usage: $0 (ISSUE) '(DESCRIPTION)'"
    exit 1
fi

FILENAME=source/upcoming_release_notes/${ISSUE}-${DESCRIPTION}.rst

pushd "$(dirname "$0")"
cp source/upcoming_release_notes/template-short.rst ${FILENAME}
if ${EDITOR} "${FILENAME}"; then
    echo "Adding ${FILENAME} to the git repository..."
    git add ${FILENAME}
fi

popd
