from setuptools import setup, find_packages

setup(
    name='rcv',
    version="0.0.1",
    description='Python utilities for Ranked Choice Voting elections and polls',
    url='https://github.com/artoonie/rcv',
    author="Armin Samii",
    author_email="armin.samii@gmail.com",

    packages=find_packages(),
    include_package_data=True,

    install_requires = [],
)
