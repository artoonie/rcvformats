#!/bin/bash
# Runs pylint and checks autopep8

myExitCode=0

pylint setup.py rcvformats

errorCode=$?
if [ $errorCode != 0 ]; then
    echo "These files must be perfectly linted"
    myExitCode=$((myExitCode+1))
fi

echo "Checking for autopep8 differences"
autopep8 --diff --exit-code --aggressive --aggressive -r --max-line-length 100 rcvformats
errorCode=$?
if [ $errorCode != 0 ]; then
    echo "You need to run autopep8:"
    echo "$> autopep8 --in-place --aggressive --aggressive -r --max-line-length 100 rcvformats"
    myExitCode=$((myExitCode+1))
fi

exit $myExitCode
