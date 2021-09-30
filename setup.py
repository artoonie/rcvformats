"""
Creates the rcvformats package
"""

import os
from setuptools import setup, find_packages

version = os.environ.get('TAG_FROM_GITHUB_ACTIONS', '0.0.0')

def readme():
    """ Returns contents of README.md """
    with open("README.md", "r+", encoding="utf-8") as file_obj:
        return file_obj.read()

setup(
    name='rcvformats',
    version=version,
    description='Schema validations, migrations, and conversions to '\
                'standardize the Ranked Choice Voting ecosystem',
    long_description=readme(),
    long_description_content_type="text/markdown",
    url='https://github.com/artoonie/rcvformats',
    author="Armin Samii",
    author_email="armin.samii@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3',
    install_requires=[
        'jsonschema',
        'openpyxl',
        'defusedxml'
    ],
    entry_points={
        'console_scripts': ['rcvformats=rcvformats.bin.cli:main'],
    }
)
