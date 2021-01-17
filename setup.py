"""
Creates the rcvformats package
"""

from setuptools import setup, find_packages

setup(
    name='rcvformats',
    version="0.0.1",
    description='Schema validations, migrations, and conversions to '\
                'standardize the Ranked Choice Voting ecosystem',
    url='https://github.com/artoonie/rcvformats',
    author="Armin Samii",
    author_email="armin.samii@gmail.com",
    packages=find_packages(),
    include_package_data=True,
)
