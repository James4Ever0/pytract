from setuptools import setup

PKG_NAME = "pytract"
# REQUIREMENTS = [
#     # "vyper",
#     "jinja2",
#     "eth-brownie",
#     "pydantic",
#     "beartype",
# ]

setup(
    name=PKG_NAME,
    version="0.0.2",
    packages=[PKG_NAME],
    description="Smart contract Python API generator.",
    url=f"https://github.com/james4ever0/{PKG_NAME}",
    package_data={PKG_NAME: ['templates/*.j2']},
    include_package_data=True,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    # install_requires=REQUIREMENTS,
    install_requires = open('requirements.txt').read().splitlines(),
    entry_points={
        'console_scripts': [
            'pytract = pytract.__main__:main',
        ],
    },
)
