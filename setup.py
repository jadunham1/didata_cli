import sys
from setuptools import setup, find_packages

wargs = {}
requires = ['libcloud']

# python 2.7 hackery
if sys.version_info <= (3, 0):
    requires.extend(
        ["future"]
    )

setup(
    author="Jeff Dunham",
    author_email="",
    description="Base description, say what your package does here",
    url="https://www.dimensiondata.com/",
    name="didata_cli",
    version="0.1.0",
    packages=find_packages(exclude=["contrib", "docs", "tests*", "tasks", "venv"]),
    install_requires=requires,
    setup_requires=[],
)
