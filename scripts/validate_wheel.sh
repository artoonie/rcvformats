#!/bin/bash
# Validates that a wheel can be built and uploaded to pypi

set -e

python3 setup.py sdist bdist_wheel
twine check dist/*
