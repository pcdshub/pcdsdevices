#!/bin/bash
ISSUE=$1
DESCRIPTION=$2
FILENAME=source/upcoming_release_notes/${ISSUE}-${DESCRIPTION}.rst

pushd "$(dirname "$0")"
cp source/upcoming_release_notes/template-short.rst ${FILENAME}
${EDITOR} ${FILENAME}
popd
