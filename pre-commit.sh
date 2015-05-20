#!/bin/bash
git stash -q --keep-index
py.test
RESULT=$?
git stash pop -q
[ $RESULT -ne 0 ] && exit 1
exit 0
