from setuptools import setup

PKG_NAME='pytract'

setup(
    name=PKG_NAME,
    version="0.0.1",
    packages=[PKG_NAME],
    description="EVM compatible smart contract language, in Python.",
    url=f"https://github.com/james4ever0/{PKG_NAME}",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[])