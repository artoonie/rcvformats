"""
Creates the rcvformats package
"""

import os
from setuptools import setup, find_packages

setup(
    name='rcvformats',
    version=os.environ['TAG_FROM_GITHUB_ACTIONS'],
    description='Schema validations, migrations, and conversions to '\
                'standardize the Ranked Choice Voting ecosystem',
    url='https://github.com/artoonie/rcvformats',
    author="Armin Samii",
    author_email="armin.samii@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3',
)
