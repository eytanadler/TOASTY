from setuptools import setup, find_packages
import re
import os

__version__ = re.findall(
    r"""__version__ = ["']+([0-9\.]*)["']+""",
    open("adfoil/__init__.py").read(),
)[0]

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "readme.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="toasty",
    version=__version__,
    description="Topology optimization of airport taxiways",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="",
    author="",
    author_email="",
    url="https://github.com/eytanadler/toasty",
    license="LGPL version 2.1",
    packages=find_packages(include=["toasty*"]),
    install_requires=[
        "numpy>=1.16",
    ],
)
