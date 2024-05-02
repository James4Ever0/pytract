from setuptools import setup
import functools

PKG_NAME = "pytract"
VERSION = "0.0.4"

# REQUIREMENTS = [
#     # "vyper",
#     "jinja2",
#     "eth-brownie",
#     "pydantic",
#     "beartype",
# ]


def merge_requirements(requirements_list: list[list[str]]):
    all_requirements = functools.reduce(lambda x, y: x + y, requirements_list)
    ret = list(set(all_requirements))
    return ret


# mandatory dependencies
PACKAGE_REQUIRES = open("requirements.txt").read().splitlines()

# extra dependencies
SIMULAR_REQUIRES = open("requirements_simular.txt").read().splitlines()

# full dependencies
ALL_REQUIRES = merge_requirements([PACKAGE_REQUIRES, SIMULAR_REQUIRES])

setup(
    name=PKG_NAME,
    version=VERSION,
    packages=[PKG_NAME],
    description="Smart contract Python API generator.",
    url=f"https://github.com/james4ever0/{PKG_NAME}",
    package_data={PKG_NAME: ["templates/*.j2"]},
    include_package_data=True,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    # install_requires=REQUIREMENTS,
    install_requires=PACKAGE_REQUIRES,
    entry_points={
        "console_scripts": [
            "pytract = pytract.__main__:main",
        ],
    },
    extras_require={"simular": SIMULAR_REQUIRES, "all": ALL_REQUIRES},
)
